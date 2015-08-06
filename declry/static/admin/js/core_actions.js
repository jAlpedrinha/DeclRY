$(function($) {
	$.fn.actions = function(opts) {
		var options = $.extend({}, $.fn.actions.defaults, opts);
		updateCounter = function() {
			var sel = $(options.actionCheckboxes).filter(":checked").length;
			$(options.counterContainer).html(interpolate(
			ngettext('%(sel)s of %(cnt)s selected', '%(sel)s of %(cnt)s selected', sel), {
				sel: sel,
				cnt: _actions_icnt
			}, true));
		}
		$(options.allToggle).on('change', function() {
			if ($(this).attr('checked')) {
				$('.action-select').attr('checked','checked')
			} else {
				$('.action-select').removeAttr('checked')
			}
			updateCounter();
		})
		$(options.actionCheckboxes).on('change', function() {
			updateCounter();
		})
		$(options.actionChoice).on('click', function(event) {
			$(options.actionInput).val($(this).data('value'))
			$(options.actionButton).click()
		})
		$(options.actionButton).hide().on('click', function(event) {
			if (! $(options.actionInput).val()) {
				event.preventDefault()	
			}			
		})
	};
	/* Setup plugin defaults */
	$.fn.actions.defaults = {
		actionContainer: "a.action-choice",
		counterContainer: "span.action-counter",
		allContainer: "div.actions span.all",
		actionChoice: ".action-choice",
		actionButton: "#action-button",
		actionShow: "#action-show",
		actionInput: "input[name=action]",
		allToggle: "#action-toggle",
		selectedClass: "selected",
		actionCheckboxes : 'tr input.action-select'
	};
});
