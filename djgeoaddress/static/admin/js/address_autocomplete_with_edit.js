/**
 * JavaScript for address autocomplete with edit mode toggle
 */
(function($) {
    'use strict';
    
    if (!$) {
        if (typeof django !== 'undefined' && django.jQuery) {
            $ = django.jQuery;
        } else {
            console.error('jQuery not available');
            return;
        }
    }
    
    function syncAddressFromAutocomplete($wrapper, addressData) {
        if (!addressData || typeof addressData !== 'object') {
            return;
        }
        
        const normalized = addressData.normalized_address || addressData;
        $wrapper.find('.address-line1').val(normalized.line1 || normalized.address_line1 || '');
        $wrapper.find('.address-line2').val(normalized.line2 || normalized.address_line2 || '');
        $wrapper.find('.address-line3').val(normalized.line3 || normalized.address_line3 || '');
        $wrapper.find('.address-postal-code').val(normalized.postal_code || '');
        $wrapper.find('.address-city').val(normalized.city || '');
        $wrapper.find('.address-state').val(normalized.state || '');
        $wrapper.find('.address-country').val(normalized.country || '');
    }
    
    function syncAddressToAutocomplete($wrapper, fieldName) {
        const addressData = {
            line1: $wrapper.find('.address-line1').val() || '',
            line2: $wrapper.find('.address-line2').val() || '',
            line3: $wrapper.find('.address-line3').val() || '',
            postal_code: $wrapper.find('.address-postal-code').val() || '',
            city: $wrapper.find('.address-city').val() || '',
            state: $wrapper.find('.address-state').val() || '',
            country: $wrapper.find('.address-country').val() || '',
        };
        
        const addressParts = [
            addressData.line1,
            addressData.line2,
            addressData.line3,
        ].filter(Boolean);
        
        const cityParts = [
            addressData.postal_code,
            addressData.city,
        ].filter(Boolean);
        
        const stateCountry = [
            addressData.state,
            addressData.country,
        ].filter(Boolean);
        
        const formattedAddress = [
            ...addressParts,
            cityParts.join(' '),
            ...stateCountry
        ].filter(Boolean).join(', ');
        
        if (formattedAddress) {
            const $select = $('select[name="' + fieldName + '"]');
            if ($select.length) {
                const select2Instance = $select.data('select2');
                if (select2Instance) {
                    const currentValue = formattedAddress;
                    
                    $select.find('option').remove();
                    const newOption = new Option(formattedAddress, currentValue, true, true);
                    $select.append(newOption);
                    $select.val(currentValue).trigger('change');
                    
                    setTimeout(function() {
                        if (select2Instance) {
                            select2Instance.trigger('select2:select', {
                                data: {
                                    id: currentValue,
                                    text: formattedAddress
                                }
                            });
                        }
                    }, 50);
                }
            }
        }
    }
    
    function initAddressToggle() {
        const $wrappers = $('.address-autocomplete-wrapper');
        if ($wrappers.length === 0) {
            return;
        }
        
        $wrappers.each(function() {
            const $wrapper = $(this);
            if ($wrapper.data('initialized')) {
                return;
            }
            $wrapper.data('initialized', true);
            
            const $autocompleteMode = $wrapper.find('.address-autocomplete-mode');
            const $editMode = $wrapper.find('.address-edit-mode');
            const $toggleEdit = $wrapper.find('.address-toggle-edit');
            const $toggleAutocomplete = $wrapper.find('.address-toggle-autocomplete');
            const fieldName = $wrapper.data('field-name');
            
            if (!$toggleEdit.length) {
                console.warn('Address toggle edit button not found');
                return;
            }
            
            const $select = $('select[name="' + fieldName + '"]');
            if ($select.length) {
                setTimeout(function() {
                    const select2Instance = $select.data('select2');
                    if (select2Instance) {
                        const currentValue = $select.val();
                        if (currentValue && currentValue.trim() !== '') {
                            const $option = $select.find('option[value="' + currentValue + '"]');
                            let displayText = '';
                            if ($option.length) {
                                displayText = $option.text() || currentValue;
                            } else {
                                displayText = currentValue;
                            }
                            
                            if (displayText) {
                                const existingData = select2Instance.data();
                                const hasValue = existingData && existingData.length > 0 && existingData[0].id === currentValue;
                                
                                if (!hasValue) {
                                    const newOption = new Option(displayText, currentValue, true, true);
                                    $select.append(newOption);
                                    $select.val(currentValue).trigger('change');
                                }
                            }
                        }
                    }
                }, 300);
            }
            
            if (!$toggleAutocomplete.length) {
                console.warn('Address toggle autocomplete button not found');
            }
            
            $toggleEdit.on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Edit button clicked, fieldName:', fieldName);
                
                let slug = null;
                
                const $hiddenInput = $('input[name="' + fieldName + '_id"]');
                if ($hiddenInput.length) {
                    slug = $hiddenInput.val();
                    console.log('Found hidden input, slug:', slug);
                } else {
                    const $select = $('select[name="' + fieldName + '"]');
                    if ($select.length) {
                        slug = $select.val();
                        console.log('Found select, slug:', slug);
                    }
                }
                
                if (slug) {
                    console.log('Fetching data for slug:', slug);
                    $.getJSON('/admin/djgeoaddress/addresslookup/autocomplete/', {
                        term: slug,
                        fetch_data: true
                    }, function(response) {
                        console.log('Response:', response);
                        if (response.data) {
                            syncAddressFromAutocomplete($wrapper, response.data);
                        } else {
                            console.warn('No data in response');
                        }
                    }).fail(function(xhr, status, error) {
                        console.warn('Could not fetch address data from cache:', error, xhr.responseText);
                    });
                } else {
                    console.warn('No slug found, cannot fetch address data');
                }
                
                $autocompleteMode.hide();
                $editMode.show();
                return false;
            });
            
            if ($toggleAutocomplete.length) {
                $toggleAutocomplete.on('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Back to autocomplete clicked');
                    syncAddressToAutocomplete($wrapper, fieldName);
                    $editMode.hide();
                    $autocompleteMode.show();
                    return false;
                });
            }
            
            if ($select.length) {
                $select.on('select2:select', function(e) {
                    const data = e.params.data;
                    console.log('Address selected in autocomplete:', data);
                    if (data && data.id) {
                        setTimeout(function() {
                            const slug = data.id;
                            console.log('Fetching data for selected slug:', slug);
                            $.getJSON('/admin/djgeoaddress/addresslookup/autocomplete/', {
                                term: slug,
                                fetch_data: true
                            }, function(response) {
                                console.log('Response for selected address:', response);
                                if (response.data) {
                                    syncAddressFromAutocomplete($wrapper, response.data);
                                }
                            }).fail(function(xhr, status, error) {
                                console.warn('Could not fetch address data:', error);
                            });
                        }, 100);
                    }
                });
            }
        });
    }
    
    $(document).ready(function() {
        setTimeout(function() {
            initAddressToggle();
        }, 100);
    });
    
    $(document).on('formset:added', function() {
        setTimeout(function() {
            initAddressToggle();
        }, 100);
    });
    
})(typeof django !== 'undefined' && django.jQuery ? django.jQuery : typeof jQuery !== 'undefined' ? jQuery : null);

