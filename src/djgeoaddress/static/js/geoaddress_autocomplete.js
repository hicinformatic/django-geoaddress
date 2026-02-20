const config = {
    cls: {
        wrapper: 'geoaddress-autocomplete-wrapper',
        hidden: 'geoaddress-autocomplete-hidden',
        editIcon: 'geoaddress-autocomplete-edit-icon',
        viewLink: 'geoaddress-autocomplete-view-link',
        dataFields: 'geoaddress-data',
        results: 'geoaddress-autocomplete-results',
        list: 'geoaddress-autocomplete-list',
        loading: 'geoaddress-autocomplete-loading',
        address: 'geoaddress-autocomplete-address',
        text_fields: [
            'address_line1',
            'address_line2',
            'address_line3',
            'city',
            'postal_code',
            'county',
            'state',
            'region',
            'country_code',
        ],
        data: {},
    },
    suffix: '_geoaddress_autocomplete',
}

const toggle = (el, show = null) => {
    const hidden = el.classList.contains(config.cls.hidden);
    if (show === true || (show === null && hidden)) {
        el.classList.remove(config.cls.hidden);
    } else {
        el.classList.add(config.cls.hidden);
    }
}


const text = (data) => {
    return config.cls.text_fields
    .map(f => data[f])
    .filter(f => f !== null && f !== undefined && f !== '')
    .join(', ');
}

const fill_data = (data, view, redirect) => {
    if(data.geoaddress_id) {
        const from_url = window.location.pathname;
        view.href = `${redirect}?from_url=${from_url}&geoaddress_id=${data.geoaddress_id}`;
        toggle(view, true);
    }else{
        toggle(view, false);
        view.href = '#';
    }
}

const getDataKey = (inputName, baseName) =>
    inputName.startsWith(baseName + '_')
        ? inputName.slice(baseName.length + 1)
        : inputName;

const fields = {};

const fetch_addresses = (name, query) => {
    let field = fields[name];
    if (!field?.list) {
        const wrapper = document.querySelector(`.${config.cls.wrapper}[name="${name}"]`);
        if (wrapper) {
            initializeGeoaddressWidget(wrapper);
            field = fields[name];
        }
    }
    if (!field?.list) return;
    field.list.innerHTML = '';
    
    if (query.length < 2) {
        toggle(field.results, false);
        return;
    }
    
    if (field.controller) field.controller.abort();
    field.controller = new AbortController();
    
    toggle(field.results, true);
    toggle(field.loading, true);

    fetch(`${field.url}?${new URLSearchParams({format: 'json', first: 1, q: query, from_url: window.location.pathname})}`, {
        signal: field.controller.signal,
        redirect: 'follow'
    })
        .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
        .then(data => {
            const addresses = data?.addresses ?? data?.results ?? [];
            addresses.forEach(address => {
                const addr = document.createElement('div');
                addr.className = config.cls.address;
                addr.textContent = text(address);
                addr.dataset.address = JSON.stringify(address);
                addr.addEventListener('click', function() {
                    const addr_json = JSON.parse(this.dataset.address);
                    field.textarea.value = this.dataset.address;
                    if (field.searchInput) field.searchInput.value = text(address);
                    field.dataInputs.forEach(input => {
                        const key = getDataKey(input.name, name);
                        input.value = addr_json[key] || '';
                    });
                    fill_data(data, field.viewLink, field.redirectUrl);
                    if (field.searchInput) field.searchInput.value = text(address);
                    toggle(field.results, false);
                });
                field.list.appendChild(addr);
            });
            toggle(field.loading, false);
            toggle(field.list, true);
        })
        .catch(error => {
            if (error.name === 'AbortError') return;
            toggle(field.loading, false);
            toggle(field.results, false);
            field.wrapper?.classList.remove(config.cls.resultsVisible);
        });
}



const initializeGeoaddressWidget = (wrapper) => {
    const name = wrapper.getAttribute('name');
    
    if (!name || name.includes('__prefix__')) {
        return;
    }
    
    // Skip if already initialized
    if (wrapper.dataset.geoaddressInitialized === 'true') {
        return;
    }
    
    const dataFields = wrapper.querySelector(`.${config.cls.dataFields}`);
    if (!dataFields) return;

    const field = {
        name,
        wrapper,
        url: wrapper.dataset.autocompleteUrl,
        redirectUrl: wrapper.dataset.redirectUrl,
        editIcon: wrapper.querySelector(`.${config.cls.editIcon}`),
        viewLink: wrapper.querySelector(`.${config.cls.viewLink}`),
        dataFields,
        results: wrapper.querySelector(`.${config.cls.results}`),
        list: wrapper.querySelector(`.${config.cls.list}`),
        loading: wrapper.querySelector(`.${config.cls.loading}`),
        searchInput: wrapper.querySelector('input[type="search"]'),
        dataInputs: Array.from(dataFields.querySelectorAll('input')),
        textarea: wrapper.querySelector('textarea'),
        controller: null,
    };

    fields[name] = field;
    
    field.dataInputs.forEach(input => {
        input.addEventListener('input', () => {
            const data = {};
            field.dataInputs.forEach(inp => {
                const key = getDataKey(inp.name, name);
                data[key] = inp.value;
            });
            data.text = text(data);
            fill_data(data, field.viewLink, field.redirectUrl);
            field.textarea.value = JSON.stringify(data);
            field.searchInput.value = data.text;
        });
    });
    

    wrapper.dataset.geoaddressInitialized = 'true';
}

const initializeAllGeoaddressWidgets = () => {
    document.querySelectorAll(`.${config.cls.wrapper}`).forEach(initializeGeoaddressWidget);
}

document.addEventListener('DOMContentLoaded', initializeAllGeoaddressWidgets);

// Edit icon click via delegation - works even if widget init failed or row added dynamically
document.addEventListener('click', (e) => {
    if (e.target.closest(`.${config.cls.editIcon}`)) {
        const wrapper = e.target.closest(`.${config.cls.wrapper}`);
        if (wrapper) {
            const dataFields = wrapper.querySelector(`.${config.cls.dataFields}`);
            if (dataFields) {
                e.stopPropagation();
                toggle(dataFields);
            }
        }
    }
});

// Nom du widget = name du textarea/name sans le suffixe _geoaddress_autocomplete
const getNameFromInput = (input) => {
    const n = input?.name;
    if (!n || !n.endsWith('_geoaddress_autocomplete')) return null;
    return n.slice(0, -'_geoaddress_autocomplete'.length);
};

// Search: lazy init + fetch via delegation - handles inline rows added after DOM ready
document.addEventListener('focusin', (e) => {
    const input = e.target;
    const name = getNameFromInput(input);
    if (!name || name.includes('__prefix__')) return;
    const wrapper = input.closest(`.${config.cls.wrapper}`);
    if (!wrapper) return;
    wrapper.setAttribute('name', name);
    if (wrapper.dataset.geoaddressInitialized !== 'true') initializeGeoaddressWidget(wrapper);
    if (fields[name]?.list) fetch_addresses(name, input.value.trim());
});

document.addEventListener('input', (e) => {
    const input = e.target;
    const name = getNameFromInput(input);
    if (!name || name.includes('__prefix__')) return;
    const wrapper = input.closest(`.${config.cls.wrapper}`);
    if (!wrapper) return;
    wrapper.setAttribute('name', name);
    if (wrapper.dataset.geoaddressInitialized !== 'true') initializeGeoaddressWidget(wrapper);
    if (fields[name]?.list) fetch_addresses(name, input.value.trim());
});

// Support for Django admin inlines - reinitialize when formset is added
// Django dispatches CustomEvent on the new row; event.target = row
document.addEventListener('formset:added', (event) => {
    const row = event.target;
    if (!row?.querySelectorAll) return;
    setTimeout(() => {
        row.querySelectorAll(`.${config.cls.wrapper}`).forEach(initializeGeoaddressWidget);
    }, 100);
});

// Also watch for dynamic additions using MutationObserver as fallback
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        mutation.addedNodes.forEach(function(node) {
            if (node.nodeType === 1) { // Element node
                // Check if the added node is a wrapper
                if (node.classList && node.classList.contains(config.cls.wrapper)) {
                    initializeGeoaddressWidget(node);
                }
                // Check if the added node contains wrappers
                if (node.querySelectorAll) {
                    node.querySelectorAll(`.${config.cls.wrapper}`).forEach(initializeGeoaddressWidget);
                }
            }
        });
    });
});

// Start observing the document for changes
if (document.body) {
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}