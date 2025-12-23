/**
 * Address autocomplete using Django admin native AutocompleteSelect widget
 * This script enhances the native autocomplete to pass the backend parameter
 */
(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Find address autocomplete fields that should use backend
        $('input[data-backend-field]').each(function() {
            var $addressInput = $(this);
            var backendFieldId = $addressInput.data('backend-field');
            var $backendField = $('#' + backendFieldId);
            
            if (!$backendField.length) {
                return;
            }
            
            // Get the Select2 instance for the address field
            var addressSelect2 = $addressInput.data('select2');
            if (!addressSelect2) {
                return;
            }
            
            // Override the ajax data function to include backend
            var originalAjaxData = addressSelect2.options.ajax.data;
            addressSelect2.options.ajax.data = function(params) {
                var data = originalAjaxData ? originalAjaxData.call(this, params) : {
                    term: params.term,
                    page: params.page || 1
                };
                
                // Add backend parameter if backend field has a value
                var backendValue = $backendField.val();
                if (backendValue) {
                    data.backend = backendValue;
                }
                
                return data;
            };
            
            // Update when backend changes
            $backendField.on('change', function() {
                // Trigger a new search if address field has a value
                if ($addressInput.val()) {
                    addressSelect2.trigger('select2:open');
                }
            });
        });
    });
})(django.jQuery);

