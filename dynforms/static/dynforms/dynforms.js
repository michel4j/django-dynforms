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
            let field_cnt = $(ctl).closest(".df-field-runtime");

            let cloned = rp_el.clone(true);
            cloned.insertAfter(rp_el);
            if (options.clearNew) {

            }
            updateRepeat(cloned);
            // rebuild chosen fields
            cloned.find("select.select option").removeAttr('selected');
            cloned.find("select.select").each(function () {
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

        // Keep multi valued fields separate, by renaming them, __# can be stripped when cleaning
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
};

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
    if (!$('#df-form-preview').is('.loaded')) {

        // Make items within each df-container sortable
        $(".df-container").sortable({
            connectWith: ".df-container", // Allows dragging between lists directly if they are visible
            placeholder: "df-field-placeholder", // Optional: CSS class for placeholder
            items: '.df-field',
            forcePlaceholderSize: true,
            start: function (event, ui) {
                ui.item.addClass("dragging-item");
                ui.item.click();
            },
            stop: function (event, ui) {
                ui.item.removeClass("dragging-item");
                let page_fields = $('.df-page.active > .df-container .df-field');
                let active_page = $('.df-page.active');
                if (ui.item.hasClass("field-btn")) {
                    ui.item.removeClass();
                    ui.item.addClass("df-field container").attr("style", "");
                    ui.item.html("");
                    ui.item.click(setupField);
                    // Ajax Add Field
                    let add_url = `${document.URL}${active_page.index()}/add/${ui.item.data('field-type')}/${ui.item.index()}/`;
                    ui.item.load(add_url, function () {
                        // renumber all fields on active page
                        page_fields.each(function () {
                            $(this).data('field-pos', $(this).index());
                        });
                        $(this).click(setupField);
                    });
                } else {
                    // move dropped field to new position on server
                    $.ajax(`${document.URL}move/`, {
                        type: 'post',
                        data: {
                            'csrfmiddlewaretoken': $('#df-builder').data('csrf-token'),
                            'from_page': active_page.index(),
                            'to_page': active_page.index(),
                            'from_pos': ui.item.data('field-pos'),
                            'to_pos': ui.item.index(),
                        },
                        success: function (result) {
                            dfToasts.success({
                                message: `Field moved to ${active_page.index()}.${ui.item.index()}!`
                            });
                        }
                    });
                    // renumber all fields on active page
                    page_fields.each(function () {
                        $(this).data('field-pos', $(this).index());
                    });
                }
            }
        }).disableSelection();

        // Make tab headers droppable
        $(".nav-tabs .nav-link").droppable({
            accept: ".df-container .df-field",  // Only accept items from our sortable lists
            hoverClass: "tab-drop-hover",       // Optional: CSS class when dragging over a tab
            tolerance: "pointer",               // Drop is triggered when a mouse pointer is over the tab
            drop: function (event, ui) {
                let $draggedItem = $(ui.draggable);
                let $targetTab = $(this);
                let $targetPage = $($targetTab.attr("href")); // Get the target pane's ID (e.g., "#tab1")


                // Prevent dropping onto the tab of the current pane
                if ($targetTab.hasClass("active")) {
                    return false; // Or handle it differently, e.g., by simply reordering if that's desired
                }
                console.log($draggedItem.data());
                $.ajax(`${document.URL}move/`, {
                    type: 'POST',
                    data: {
                        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                        'from_page': $draggedItem.data('field-page') - 1,
                        'to_page': $targetPage.data('page-number') - 1,
                        'from_pos': $draggedItem.data('field-pos'),
                        'to_pos': 0,
                    },
                    dataType: 'json',
                    success: function () {
                        window.location.reload();
                    }
                });

                // // Append the dragged item to the target list
                // $targetList.append($draggedItem);
                //
                // // Activate the target tab
                // let tab = new bootstrap.Tab($targetTab[0]); // Get the Bootstrap Tab instance
                // tab.show();
                //
                // // Optional: Refresh sortable on the target list if items were added/removed
                // // $targetList.sortable("refresh");
                // // $(".sortable-list").sortable("refreshPositions"); // Might be needed in some cases
            }
        });

        // Make field buttons draggable to containers
        $('.field-btn').draggable({
            connectToSortable: '.df-page.active > .df-container',
            revert: "invalid",
            appendTo: '.df-page.active > .df-container',
            cursorAt: {left: 5, top: 5},
            scroll: true,
            helper: "clone",
            start: function (event, ui) {
                let exp = $('.df-page.active > .df-container');
                ui.helper.addClass("ui-draggable-helper");
                ui.helper.width(exp.width() / 4);
            },
            drag: function (event, ui) {
                ui.position.top = NaN;
            }
        }).click(function () {
            if ($(this).is('.ui-draggable-dragging')) {
                return;
            }
            const new_el = $('<div class="df-field"></div>');
            const cur_page = $('.df-page.active');
            const cur_container = $('.df-page.active > .df-container');
            cur_container.append(new_el);
            new_el.data('field-type', $(this).data('field-type'));
            new_el.data('field-pos', new_el.index());
            new_el.click(setupField);

            // Ajax Add Field
            let field_url = `${document.URL}${cur_page.index()}/add/${new_el.data('field-type')}/${new_el.index()}/`;
            new_el.load(field_url, function () {
                $(this).click();
            });
        }).disableSelection();

        $('.df-field').click(setupField);
        setupMenuForm("#form-settings .df-menu-form");
        setupMenuForm("#field-settings .df-menu-form");

        $(document).on('click', "button[data-page-number]", function (e) {
            e.preventDefault();
            $.ajax(`${document.URL}${$(this).data('page-number')}/del/`, {
                type: 'post',
                data: {
                    'csrfmiddlewaretoken': $('#df-builder').data('csrf-token'),
                },
                success: function (result) {
                    dfToasts.success({
                        message: `Page Deleted!`
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
            let active_field = $('div.df-field.selected');
            let active_page = $('.df-page.active');
            let next_page = Math.min(active_page.index() + 1, $('.df-page').last().index());
            $.ajax(`${document.URL}move/`, {
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                    'from_page': active_page.index(),
                    'to_page': next_page,
                    'from_pos': active_field.index(),
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
            let cur_fld = $('div.df-field.selected');
            let page_no = $('.df-page.active').index();
            $.ajax(`${document.URL}move/`, {
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                    'from_page': page_no,
                    'to_page': Math.max(page_no - 1, 0),
                    'from_pos': cur_fld.index(),
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
            return (first == second);
        case "iexact":
            return (typeof first == 'string' ? first.toLowerCase() === second.toLowerCase() : false);
        case "neq":
            return (first != second);
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
            return (first.indexOf(second) == 0);
        case "istartswith":
            return (typeof first == 'string' ? first.toLowerCase().indexOf(second.toLowerCase()) == 0 : false);
        case "endswith":
            return (first.slice(-second.length) == second);
        case "iendswith":
            return (typeof first == 'string' ? first.toLowerCase().slice(-second.length) == second.toLowerCase() : false);
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

$(document).on("keypress", ":input:not(textarea):not([type=submit])", function (event) {
    return event.keyCode !== 13;
});
