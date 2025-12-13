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
    
    function buildReferenceSlug(backendUsed, backendReference) {
        if (!backendReference || !backendUsed) {
            return null;
        }
        function encodeToken(value) {
            const safeChars = '._~:@';
            let encoded = '';
            for (let i = 0; i < value.length; i++) {
                const char = value[i];
                if (safeChars.indexOf(char) !== -1) {
                    encoded += char;
                } else {
                    encoded += encodeURIComponent(char);
                }
            }
            return encoded;
        }
        const backendToken = encodeToken(String(backendUsed).trim());
        const referenceToken = encodeToken(String(backendReference).trim());
        if (!backendToken || !referenceToken) {
            return null;
        }
        return backendToken + '-' + referenceToken;
    }
    
    function updateMetadataDisplay($wrapper, adminUrl) {
        const confidence = $wrapper.find('.address-confidence').val() || '';
        const relevance = $wrapper.find('.address-relevance').val() || '';
        const backendUsed = $wrapper.find('.address-backend-used').val() || '';
        const backendReference = $wrapper.find('.address-backend-reference').val() || '';
        
        $wrapper.find('.address-confidence-display').text(confidence ? parseFloat(confidence).toFixed(2) : '—');
        $wrapper.find('.address-relevance-display').text(relevance ? parseFloat(relevance).toFixed(2) : '—');
        $wrapper.find('.address-backend-used-display').text(backendUsed || '—');
        
        const $referenceLink = $wrapper.find('.address-backend-reference-link');
        if (backendReference) {
            let url = adminUrl;
            if (!url) {
                const slug = buildReferenceSlug(backendUsed, backendReference);
                if (slug) {
                    url = '/admin/djgeoaddress/addresslookup/' + slug + '/change/';
                }
            }
            if (url) {
                $referenceLink.attr('href', url);
                $referenceLink.text(backendReference);
            } else {
                $referenceLink.attr('href', '#');
                $referenceLink.text(backendReference);
            }
        } else {
            $referenceLink.attr('href', '#');
            $referenceLink.text('—');
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
        $wrapper.find('.address-municipality').val(normalized.municipality || normalized.extras?.municipality || '');
        $wrapper.find('.address-confidence').val(normalized.confidence || '');
        $wrapper.find('.address-relevance').val(normalized.relevance || '');
        $wrapper.find('.address-backend-used').val(normalized.backend_used || normalized.backend || '');
        $wrapper.find('.address-backend-reference').val(normalized.backend_reference || normalized.address_reference || '');
        
        const adminUrl = normalized.admin_url || addressData.admin_url;
        updateMetadataDisplay($wrapper, adminUrl);
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
            
            function clearBackendFields() {
                $wrapper.find('.address-confidence').val('');
                $wrapper.find('.address-relevance').val('');
                $wrapper.find('.address-backend-used').val('');
                $wrapper.find('.address-backend-reference').val('');
                updateMetadataDisplay($wrapper, null);
            }
            
            const $addressFields = $wrapper.find('.address-line1, .address-line2, .address-line3, .address-postal-code, .address-city, .address-state, .address-country, .address-municipality');
            $addressFields.on('input change', function() {
                clearBackendFields();
            });
            
            // Get admin_url from data attribute if available (for existing addresses)
            const initialAdminUrl = $wrapper.data('admin-url') || null;
            updateMetadataDisplay($wrapper, initialAdminUrl);
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

