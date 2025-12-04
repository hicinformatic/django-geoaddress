/**
 * Address autocomplete using Django's Select2 (native admin autocomplete)
 */
(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Find all address autocomplete inputs
        $('.address-autocomplete').each(function() {
            var $input = $(this);
            var autocompleteUrl = $input.data('autocomplete-url');
            
            if (!autocompleteUrl) {
                console.warn('Address autocomplete URL not found');
                return;
            }
            
            // Initialize Select2 autocomplete (Django admin includes Select2)
            $input.select2({
                ajax: {
                    url: autocompleteUrl,
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            q: params.term,
                            page: params.page || 1,
                            limit: 10
                        };
                    },
                    processResults: function(data) {
                        if (data.error) {
                            console.error('Address autocomplete error:', data.error);
                            return {results: []};
                        }
                        return {
                            results: data.results || []
                        };
                    },
                    cache: true
                },
                minimumInputLength: 3,
                placeholder: 'Start typing an address...',
                allowClear: true,
                width: '100%'
            });
            
            // Handle selection to populate hidden address fields if they exist
            $input.on('select2:select', function(e) {
                var data = e.params.data;
                console.log('Address selected:', data);
                
                // If there are hidden fields for address components, populate them
                var $form = $input.closest('form');
                if (data.line1) $form.find('[name$="_line1"]').val(data.line1);
                if (data.line2) $form.find('[name$="_line2"]').val(data.line2);
                if (data.postal_code) $form.find('[name$="_postal_code"]').val(data.postal_code);
                if (data.city) $form.find('[name$="_city"]').val(data.city);
                if (data.state) $form.find('[name$="_state"]').val(data.state);
                if (data.country) $form.find('[name$="_country"]').val(data.country);
                if (data.latitude) $form.find('[name$="_latitude"]').val(data.latitude);
                if (data.longitude) $form.find('[name$="_longitude"]').val(data.longitude);
            });
        });
    });
})(django.jQuery);

