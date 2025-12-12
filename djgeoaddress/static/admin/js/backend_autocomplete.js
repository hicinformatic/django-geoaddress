/**
 * Backend autocomplete using Django's Select2 (native admin autocomplete)
 */
(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Find all backend autocomplete inputs
        $('.backend-autocomplete').each(function() {
            var $input = $(this);
            var autocompleteUrl = $input.data('autocomplete-url');
            
            if (!autocompleteUrl) {
                console.warn('Backend autocomplete URL not found');
                return;
            }
            
            // Get initial value and display name if available
            var initialValue = $input.val();
            var displayName = $input.data('display-name');
            
            // Initialize Select2 autocomplete (Django admin includes Select2)
            var select2Options = {
                ajax: {
                    url: autocompleteUrl,
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            q: params.term,
                            page: params.page || 1
                        };
                    },
                    processResults: function(data) {
                        if (data.error) {
                            console.error('Backend autocomplete error:', data.error);
                            return {results: []};
                        }
                        // Django admin autocomplete returns {results: [{id: ..., text: ...}, ...]}
                        return {
                            results: (data.results || []).map(function(item) {
                                return {
                                    id: item.id || item.text,
                                    text: item.text || item.id
                                };
                            })
                        };
                    },
                    cache: true
                },
                minimumInputLength: 0, // Allow showing all backends on focus
                placeholder: 'Select a backend...',
                allowClear: true,
                width: '100%'
            };
            
            // If we have an initial value, set it
            if (initialValue && displayName) {
                select2Options.data = [{
                    id: initialValue,
                    text: displayName
                }];
            }
            
            $input.select2(select2Options);
        });
    });
})(django.jQuery);

