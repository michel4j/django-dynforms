function createMultiSelect(selector) {
    let sel = $(selector);
    sel.selectize({plugins: ['remove_button'],});
}

function destroyMultiSelect(selector) {
    $(selector).selectize('destroy');
}


// Handle Repeats
(function ($) {
    $.fn.extend({
        repeatable: function (options) {
            options = $.extend({}, $.repeatable.defaults, options);
            this.each(function () {
                new $.repeatable(this, options);
            });
            return this;
        }
    });

    // ctl is the element, options is the set of defaults + user options
    $.repeatable = function (ctl, options) {

        let rp_sel = $(ctl).data("repeat-add");
        let all_rp = $(ctl).siblings(rp_sel);
        let all_rp_rm = all_rp.find(options.remove);

        function updateRepeat(section) {

            section.find('.repeat-html-index').each(function () {
                $(this).html(section.index());
            });
            section.find('.repeat-value-index').each(function () {
                $(this).attr('value', section.index());
            });
            section.find('[data-repeat-index]').each(function () {
                $(this).attr('data-repeat-index', section.index());
            });
            section.find(':input').each(function () {
                $(this).attr('id', $(this).attr('id') + "_" + section.index());
            });
            section.find('label').each(function () {
                let lbl = $(this);
                if (lbl.attr('for')) {
                    lbl.attr('for', lbl.attr('for') + "_" + section.index());
                }
            });
            section.attr('id', section.attr('id') + "_" + section.index())

            all_rp = $(ctl).siblings(rp_sel);

            all_rp_rm = all_rp.find(options.remove);

            if (all_rp.length > 1) {
                all_rp_rm.removeAttr("disabled");
            } else {
                all_rp_rm.attr("disabled", "disabled");
            }

            // rename multivalued field names so values are kept separate
            all_rp.each(function (idx, obj) {
                $(this).find("[data-repeat-name]").each(function () {
                    $(this).attr("name", $(this).data("repeat-name") + "." + idx);
                });
            });
        }

        $(ctl).click(function (e) {
            let rp_el = all_rp.last();
            let cloned = rp_el.clone(true);
            cloned.insertAfter(rp_el);
            if (options.clearNew) {

            }
            updateRepeat(cloned);
            // reset select fields
            cloned.find("select option").removeAttr('selected');
            cloned.find("select").each(function () {
                $(this).val('');
                $(this).trigger('change')
            });
        });

        all_rp_rm.each(function () {
            $(this).click(function (e) {
                let del_el = $(this).closest(rp_sel);
                let others = del_el.siblings(rp_sel);
                if (others.length > 0) {
                    del_el.slideUp('fast', function () {
                        del_el.remove();
                        others.each(function () {
                            updateRepeat($(this));
                        });
                    });
                } else if (options.clearIfLast) {
                    del_el.find(":input").each(function () {
                        $(this).val('').removeAttr('checked').removeAttr('selected');
                    })
                }
                ;
            });
        });

        if (all_rp.length > 1) {
            all_rp_rm.removeAttr("disabled");
        } else {
            all_rp_rm.attr("disabled", "disabled");
        }

        // Keep multivalued fields separate, by renaming them, __# can be stripped when cleaning
        // the data
        all_rp.each(function (idx, obj) {
            $(obj).find("select[multiple]:not([data-repeat-name])").each(function () {
                $(this).data("repeat-name", $(this).attr("name"));
                $(this).attr("name", $(this).data("repeat-name") + "." + idx);
            });
        });

    };

    // option defaults
    $.repeatable.defaults = {
        remove: ".remove-repeat",
        clearIfLast: true,
        clearNew: true
    };
})(jQuery);


// field preview customizer
function setupField() {

    if ($(this).is(".selected")) {
        return;
    }
    let prev_field = $('.df-field.selected');
    let active_field = $(this);
    let active_page = $('.df-page.active');
    let rules_url = `${document.URL}${active_page.index()}/rules/${active_field.data('field-pos')}/`;
    let put_url = `${document.URL}${active_page.index()}/put/${active_field.data('field-pos')}/`;

    // remove selected class from all fields
    prev_field.toggleClass("selected", false);
    active_field.toggleClass("selected", true);

    // load field settings
    $('#df-sidebar a[href="#field-settings"]').tab('show');

    // Ajax Update form
    $("#field-settings").load(put_url, function () {
        setupMenuForm("#field-settings .df-menu-form");
        $('#field-settings #edit-rules').attr('data-modal-url', rules_url);
    });
}

// Form customization for each form
function setupMenuForm(form_id) {

    // Setup Repeatable Fields
    $(`${form_id} button[data-repeat-add]`).repeatable({clearIfLast: false});


    // handle applying field settings
    function submitHandler(event) {
        let active_page = $('.df-page.active');
        let active_field = $('div.df-field.selected');
        let put_url = `${document.URL}${active_page.index()}/put/${active_field.index()}/`;
        let get_url = `${document.URL}${active_page.index()}/get/${active_field.index()}/`;
        $(form_id).ajaxSubmit({
            type: 'post',
            url: put_url,
            success: function (result) {
                active_field.load(get_url, function () {
                    adjustFieldWidth(active_field);
                });
                $("#field-settings").html(result);
                setupMenuForm("#field-settings .df-menu-form");
            }
        });
    }

    $(form_id + ' button[name="apply-field"]').click(submitHandler);
    $(form_id + ' :input').each(function () {
        $(this).change(submitHandler);
    });
}

function adjustFieldWidth(selector) {
    const element = $(selector);
    let child = $(element).children('.form-group');
    element.removeClass(element.data('field-width')).addClass(child.data('field-width'));
    element.data('field-width', child.data('field-width'));
}

// Load the form builder
function doBuilderLoad() {
    $('body').attr('data-df-builder', 'true');
    if (!$('#df-form-preview').is('.loaded')) {

        // Make items within each df-container sortable
        $(".df-container").sortable({
            connectWith: ".df-container",           // Allows dragging between lists directly if they are visible
            placeholder: "df-field-placeholder",    // Optional: CSS class for placeholder
            items: '.df-field',
            forcePlaceholderSize: true,
            revert: true,
            start: function (event, ui) {
                ui.item.addClass("dragging-item");
                ui.item.click();
            },
            update: function (event, ui) {
                ui.item.removeClass("dragging-item");
                let draggedItem = $(ui.item);
                let activePage = $('.df-page.active');
                if (!draggedItem.hasClass('stop-sorting')) {
                    $.ajax(`${document.URL}move/`, {
                        type: 'post',
                        data: {
                            'csrfmiddlewaretoken': $('#df-builder').data('csrf-token'),
                            'from_page': activePage.index(),
                            'to_page': activePage.index(),
                            'from_pos': ui.item.data('field-pos'),
                            'to_pos': ui.item.index(),
                        },
                        success: function (result) {
                            // renumber all fields on active page
                            $('.df-page > .df-container > .df-field').each(function () {
                                $(this).data('field-pos', $(this).index());
                            });
                            dfToasts.success({
                                message: `Field moved to Position ${ui.item.index()}!`
                            });
                        }
                    });
                }
            }
        }).disableSelection();

        // Make tab headers droppable
        $("#df-form-preview .nav-tabs .nav-link").droppable({
            accept: ".df-container .df-field",  // Only accept items from our sortable lists
            hoverClass: "tab-drop-hover",       // Optional: CSS class when dragging over a tab
            tolerance: "pointer",               // Drop is triggered when a mouse pointer is over the tab
            drop: function (event, ui) {
                let draggedItem = $(ui.draggable);
                let targetTab = $(this);
                let targetPage = $(targetTab.attr("href")); // Get the target pane's ID (e.g., "#tab1")
                let targetList = targetPage.find('.df-container'); // Find the sortable list in the target pane

                // notify sortable not to handle this drop
                draggedItem.addClass("stop-sorting");

                // Prevent dropping onto the tab of the current pane
                if (targetTab.hasClass("active")) {
                    return false; // Or handle it differently, e.g., by simply reordering if that's desired
                }

                $.ajax(`${document.URL}move/`, {
                    type: 'POST',
                    data: {
                        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                        'from_page': draggedItem.data('field-page') - 1,
                        'to_page': targetPage.index(),
                        'from_pos': draggedItem.data('field-pos'),
                        'to_pos': 0,
                    },
                    success: function () {
                        dfToasts.success({
                            message: `Field moved to Page ${targetPage.data('page-number')}!`
                        });
                    }
                });

                // Activate the target tab
                let tab = new bootstrap.Tab(targetTab[0]); // Get the Bootstrap Tab instance
                tab.show();

                // prepend the dragged item to the target list
                draggedItem.removeClass("dragging-item ui-sortable-helper");
                draggedItem.removeAttr("style"); // Remove any inline styles

                let newItem = draggedItem.clone(true);
                newItem.data('field-page', targetPage.index() + 1); // Update the page index
                targetList.prepend(newItem);
                draggedItem.remove(); // remove item from dom
                targetList.sortable("refresh");

                // renumber all fields
                $('.df-page > .df-container > .df-field').each(function () {
                    $(this).data('field-pos', $(this).index());
                });
            }
        });

        // Make field buttons draggable to containers
        $('.field-btn').click(function () {
            if ($(this).is('.ui-draggable-dragging')) {
                return;
            }
            const newField = $('<div class="df-field"></div>');
            const curPage = $('.df-page.active');
            const curContainer = $('.df-page.active > .df-container');
            curContainer.append(newField);
            newField.data('field-type', $(this).data('field-type'));
            newField.data('field-pos', newField.index());
            newField.click(setupField);

            // Ajax Add Field
            let field_url = `${document.URL}${curPage.index()}/add/${newField.data('field-type')}/${newField.index()}/`;
            newField.load(field_url, function () {
                $(this).click();
            });
        });

        $('.df-field').click(setupField);
        setupMenuForm("#form-settings .df-menu-form");
        setupMenuForm("#field-settings .df-menu-form");

        $(document).on('click', "button[data-page-number]", function (e) {
            let page_number = $(this).data('page-number');
            e.preventDefault();
            $.ajax(`${document.URL}${page_number}/del/`, {
                type: 'post',
                data: {
                    'csrfmiddlewaretoken': $('#df-builder').data('csrf-token'),
                },
                success: function (result) {
                    dfToasts.success({
                        message: `Page ${page_number} Deleted!`
                    });
                }
            });
            window.location.reload();
        });

        $("#df-form-preview").addClass("loaded");

        // handle deleting fields
        $(document).on('click', '#field-settings #delete-field', function (e) {
            e.preventDefault();
            // handle deleting fields
            const active_field = $('.df-field.selected');
            const active_page = $('.df-page.active');
            const page_fields = $('.df-page.active > .df-container .df-field');
            let del_url = `${document.URL}${active_page.index()}/del/${active_field.index()}/`;

            $.ajax(del_url, {
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                },
                success: function (response) {
                    dfToasts.success({
                        message: `Field: ${active_field.data('field-type')} deleted!`
                    });
                    active_field.remove();
                    // renumber all fields on active page
                    page_fields.each(function () {
                        $(this).data('field-pos', $(this).index());
                    });
                    $("#field-settings").html(response);
                },
                error: function (xhr, status, error) {
                    dfToasts.error({
                        message: error,
                        title: "Error deleting field!"
                    });
                }
            });
        });

        // Move field to next page
        $(document).on('click', "#field-settings #move-next", function (e) {
            e.preventDefault();
            let activeField = $('div.df-field.selected');
            let activePage = $('.df-page.active');
            let nextPage = Math.min(activePage.index() + 1, $('.df-page').last().index());
            $.ajax(`${document.URL}move/`, {
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                    'from_page': activePage.index(),
                    'to_page': nextPage,
                    'from_pos': activeField.index(),
                    'to_pos': 0,
                },
                dataType: 'json',
                success: function () {
                    window.location.reload();
                }
            });
        });

        //
        $(document).on('click', "#field-settings #move-prev", function (e) {
            e.preventDefault();
            let curField = $('div.df-field.selected');
            let pageNumber = $('.df-page.active').index();
            $.ajax(`${document.URL}move/`, {
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                    'from_page': pageNumber,
                    'to_page': Math.max(pageNumber - 1, 0),
                    'from_pos': curField.index(),
                    'to_pos': 0,
                },
                dataType: 'json',
                success: function () {
                    window.location.reload();
                }
            });
        });

    }

};


function testRule(first, operator, second) {
    switch (operator) {
        case "lt":
            return (first < second);
        case "lte":
            return (first <= second);
        case "exact":
            return (first === second);
        case "iexact":
            return (typeof first == 'string' ? first.toLowerCase() === second.toLowerCase() : false);
        case "neq":
            return (first !== second);
        case "gte":
            return (first >= second);
        case "eq" :
            return (first === second);
        case "gt" :
            return (first > second);
        case "in" :
            return (second.indexOf(first) >= 0);
        case "contains" : {
            return (first != null ? (typeof first == 'array' ? $.inArray(second, first) : first.indexOf(second) >= 0) : false);
        }
        case "startswith":
            return (first.indexOf(second) === 0);
        case "istartswith":
            return (typeof first == 'string' ? first.toLowerCase().indexOf(second.toLowerCase()) == 0 : false);
        case "endswith":
            return (first.slice(-second.length) === second);
        case "iendswith":
            return (typeof first == 'string' ? first.toLowerCase().slice(-second.length) === second.toLowerCase() : false);
        case "nin":
            return !(second.indexOf(first) >= 0);
        case "isnull":
            return !(first);
        case "notnull":
            return !(!(first));
    }
}

function valuesOnly(va) {
    let value = [];
    if (va.length === 1) {
        return va[0].value;
    }
    if (va.length === 0) {
        return null;
    }
    $(va).each(function () {
        value.push(this.value)
    });
    return value;
}

function guardDirtyForm(selector) {
    let formInstance = $(selector);
    formInstance.find("a[data-bs-toggle='tab']").click(function (e) {
        formInstance.find(":input[name='active_page']").val($(this).data('page-number'));
    });

    $("a[data-tab-proxy]").click(function (e) {
        $($(this).attr('data-tab-proxy')).click();
    });

    //Save time when form was loaded
    formInstance.attr('data-df-loaded', $.now());

    function monitorChanges(event) {
        // save time when any field was modified except while loading
        let dur = Math.abs(event.timeStamp - formInstance.attr('data-df-loaded'));
        if (dur > 2000) {
            $(selector).attr('data-df-dirty', dur);
        }
    }

    formInstance.on('change', ':input', monitorChanges);
    formInstance.on('click', '[data-repeat-add], .remove-repeat', monitorChanges);

    formInstance.submit(function () {
        $(this).removeAttr('data-df-dirty'); // No warning when saving dirty form
        $("input[disabled]").removeAttr("disabled");
    });
    $(".df-field").click(function () {
        $('.df-field').removeClass('activated');
        $(this).addClass('activated');
    });
}


/**
 * jQuery Form Progress Plugin
 *
 * This plugin monitors an HTML form and calculates its completion percentage
 * based on the number of filled or selected input fields.
 *
 * Usage:
 * $(document).ready(function() {
 * $('#myForm').formProgress({
 * update: function(percentAll, percentRequired) {
 * // 'this' inside this function refers to the form element.
 * // You can update a progress bar or text here.
 * $('#progressBar').css('width', percentRequired + '%').text(Math.round(percentRequired) + '% Complete');
 * console.log('Form completion: ' + percentRequired.toFixed(2) + '%');
 * }
 * });
 * });
 *
 * @param {object} options - Configuration options for the plugin.
 * @param {function} [options.update] - A callback function that is executed
 * whenever the form's completion percentage changes.
 * It receives the total percentage as it's first argument, and the percentage of required fields
 * as it's second argument 'this' inside the callback
 * will refer to the form DOM element.
 */
(function ($) {
    $.fn.formProgress = function (options) {

        // Default options
        let settings = $.extend({
            update: null // Default update function is null
        }, options);

        // Iterate over each form selected by the jQuery object
        return this.each(function () {
            const $form = $(this); // Current form element

            /**
             * Calculates the completion percentage of the form.
             * @returns {number} The completion percentage (0-100).
             */
            function calculateProgress() {
                let completedFields = new Set();
                let requiredFields = new Set();
                let allFields = new Set(); // Total number of relevant fields

                // Select all relevant input fields within the form
                // Exclude buttons, resets, submits, and hidden fields
                $form.find(':input[name]:not([type="button"], [type="submit"], [type="reset"], [type="hidden"], .hidden, .df-hide :input)')
                    .each(function () {
                        const $field = $(this);
                        let fieldValue = ""; // Initialize field value

                        allFields.add($field.attr('name')); // add field name to the set of all fields

                        // Check if the field is required
                        if ($field.is('[required], .required')) {
                            requiredFields.add($field.attr('name'));
                        }

                        // Check if the field is completed
                        if ($field.is('input[type="checkbox"], input[type="radio"]')) {
                            // For checkboxes and radio buttons, check if they are checked
                            fieldValue = $field.is(':checked') ? $field.val() : ""; // Get the value if checked, otherwise empty
                        } else if ($field.is('input[type="text"], input[type="password"], input[type="email"], input[type="tel"], input[type="url"], input[type="number"], textarea')) {
                            // For text-based inputs and text areas, check if they have a value
                            fieldValue = $field.val() ? $field.val().trim() : "";
                        } else  if ($field.is('select')) {
                            // For select elements, check if a value is selected
                            fieldValue = $field.val() ? `${$field.val()}`.trim() : ""; // Get the trimmed value of the selected option
                        }

                        // Add more field types here if necessary

                        if (fieldValue !== "") {
                            // If the field has a value, consider it completed
                            completedFields.add($field.attr('name'));
                        }
                    });

                // Calculate the percentage
                const percentAll = (allFields.size > 0) ? (allFields.intersection(completedFields).size / allFields.size) * 100 : 100;
                const percentRequired = (requiredFields.size > 0) ? (requiredFields.intersection(completedFields).size / requiredFields.size) * 100 : 100;

                // If an update callback is provided in options, call it
                if (typeof settings.update === 'function') {
                    // Call the update function with 'this' pointing to the form element
                    settings.update.call($form[0], percentAll, percentRequired);
                }

                return percentAll;
            }

            // Bind events to trigger progress calculation
            // 'input' event for text fields; 'change' for selects/checkboxes/radios
            // 'keyup' is added for broader compatibility, though 'input' is generally preferred.
            $form.on('input change keyup', 'input, select, textarea', function () {
                calculateProgress();
            });

            // Perform an initial calculation when the plugin is first applied
            calculateProgress();
        });
    };
})(jQuery);

$(document).on("keypress", ":input:not(textarea):not([type=submit])", function (event) {
    return event.keyCode !== 13;
});
