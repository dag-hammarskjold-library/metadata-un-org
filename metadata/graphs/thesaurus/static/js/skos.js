customElements.define('skos-header',
    class extends HTMLElement {
        constructor(data) {
            super();
            this.attachShadow({ mode: 'open' });
            const skosHeaderTemplate = document.getElementById('skos-header');
            const skosHeaderContent = skosHeaderTemplate.content;
            const h4 = skosHeaderContent.querySelector("div.h4");
            h4.innerText = data;
            //const recordFieldContent = recordFieldTemplate.content;
            //const tagSpan = recordFieldContent.querySelector("span#tag");
            //tagSpan.innerText = tag;
            //const tagDataSpan = recordFieldContent.querySelector("span#subfield");
            //tagDataSpan.innerText = tagData;
            this.shadowRoot.appendChild(skosHeaderContent.cloneNode(true));
        }
    }
);

customElements.define('skos-pref-abel', 
    class extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
        }
    }
);
//customElements.define('skos-scopeNote');
//customElements.define('skos-broader');
//customElements.define('skos-narrower');
//customElements.define('skos-related');

customElements.define('skos-concept',
    class extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
            this.aboutURI = `${this.getAttribute('about')}`;
            this.fetchURI = `${this.getAttribute('fetch')}`;
            this.lang = `${this.getAttribute('lang')}`;
        }

        connectedCallback() {
            this.loadData(this.fetchURI);
        }

        loadData(dataUrl) {
            return new Promise((res, rej) => {
                fetch(dataUrl, {
                    headers: {
                        'Accept': 'application/ld+json'
                    }
                })
                .then(data => data.json())
                .then((json) => {
                    this.buildConcept(json);
                    //console.log(json['result'])
                    //res();
                })
                .catch((error) => rej(error));
            })
        }

        buildConcept(conceptData) {
            
            

            var header = null;
            conceptData['skos:prefLabel'].forEach(pl => {
                if (pl['@language'] == this.lang) {
                    header = pl["@value"];
                }
            });

            const SKOSHeaderEl = customElements.get('skos-header');
            const skosHeader = new SKOSHeaderEl(header);
            this.shadowRoot.appendChild(skosHeader);

            //const SKOSConceptEl = customElements.get('skos-concept');
            //const skosConceptEl = new SKOSConceptEl();

            //console.log(conceptData['skos:prefLabel']);

            //this.shadowRoot.appendChild(skosConceptEl);

        }

    }
);