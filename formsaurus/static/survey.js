$.fn.enterKey = function (fnc) {
    return this.each(function () {
        $(this).keypress(function (ev) {
            var keycode = (ev.keyCode ? ev.keyCode : ev.which);
            if (keycode == '13') {
                fnc.call(this, ev);
            }
        })
    })
}

function render_tmpl(tmpl_id, question) {
    if (!$(tmpl_id).length) {
        console.log('Template ' + tmpl_id + ' not found within the page')
        return ''
    }
    return Mustache.render($(tmpl_id).html(), question)
}

var template_map = {
    'WS': 'welcome_screen',
    'TS': 'thank_you_screen',
    'MC': 'multiple_choice',
    'PN': 'phone_number',
    'ST': 'short_text',
    'LT': 'long_text',
    'S_': 'statement',
    'YN': 'yes_no',
    'E_': 'email',
    'OS': 'opinion_scale',
    'R_': 'rating',
    'D_': 'date',
    'N_': 'number',
    'DD': 'dropdown',
    'L_': 'legal',
    'FU': 'file_upload',
    'P_': 'payment',
    'W_': 'website',
}

function render_question(question) {
    console.log('Render', question)
    if (!question.type in template_map) {
        console.log('Question type ' + question.type + ' not supported')
        return ''
    }
    var key = '#' + template_map[question.type] + '_template';
    return render_tmpl(key, question)
}

var current_index = 0;

function render_current_question(questions) {
    var question = questions[current_index];
    var html = render_question(question);
    // console.log(html)
    $('#qs').html('')
    $('#qs').html(html)

    $('.dropdown').select2({
        allowClear: true,
        placeholder: 'Select an option',
    });
    if (question.type == 'D_') {
        console.log('picker.format = ' + question.parameters.format)
        var picker = new Pikaday({
            field: $('.datepicker')[0],
            format: question.parameters.format,
            onSelect: function() {
                console.log(this.getMoment().format(question.parameters.format));
            }   
        });
    
    }


    form = $('#qs').find('form')
    form.submit(function() {
        console.log('Form submitted')
        current_index = current_index + 1; // Once we have logic, this will change!
        render_current_question(questions)
        return false;
    });
    // Multiple choice
    if (question.type == 'MC') {
        form.find('input').click(function () {
            var elt = $(this);
            if (elt.hasClass('btn-primary')) {
                elt.addClass('btn-secondary').removeClass('btn-primary');
                return false;
            }
            if (!question.parameters.multiple_selection) {
                form.find('input').removeClass('btn-primary').addClass('btn-secondary');
            }
            elt.addClass('btn-primary').removeClass('btn-secondary');
            if (!question.parameters.multiple_selection) {
                form.submit();
            }
            return false;
        })    
    } else if (question.type == 'YN' || question.type == 'OS' || question.type == 'R_' || question.type == 'L_') {
        form.find('input, button').click(function() {
            var elt = $(this)
            elt.addClass('btn-primary').removeClass('btn-secondary')
            form.submit()
            return false;
        })
    } else {
        form.find('textarea').keyup(function() {
            this.style.height = (this.scrollHeight)+"px";
        })

        form.find('input').enterKey(function() {
            console.log('input.enterKey() -> Next Page');
            form.submit()
            return false
        })
    }

}

function install_questions(questions) {
    console.log('questions = ', questions)
    render_current_question(questions);
}

$(function() {
    var id = $('#survey_id').val();
    console.log('survey_id = ' + id);
    $.get("/questions/" + id, function(data) {
        install_questions(data.questions)
    });
})