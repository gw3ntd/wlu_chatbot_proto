// Must have 
// <script type="module" src="../static/js/main.js"></script> 
// at the head of the HTML file to use this module

// Header at the top of every page
class scottyHeader extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <style>
                * {
                box-sizing: border-box;
                }
                body {
                margin: 0;
                font-family: "Fira Sans", sans-serif;
                height: 100vh;
                background-color: #f7f7f8;
                color: #333;
                display: flex;
                flex-direction: column; 
                }

                /* HEADER */
                header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background-color: #003da5;
                color: white;
                padding: 1.5rem 1.5rem;
                }
                .header-left {
                display: flex;
                align-items: center;
                gap: 1rem; 
                }
                header h1 {
                margin: 0;
                font-family: "Oswald", sans-serif;
                font-weight: 500;
                }
                header img {
                height: 50px;
                }
                h1 span {
                color: #FFB81C; 
                }

                /* FONTS */
                .oswald {
                font-family: "oswald", sans-serif;
                font-optical-sizing: auto;
                font-weight: 400;
                font-style: normal;
                }
                .fira-sans {
                font-family: "Fira Sans", sans-serif;
                font-weight: 400;
                font-style: normal;
                }
            </style>

            <header>
                <h1>Scott<span><b>GPT</b></span></h1>
                <img src="../static/images/UC_Riverside_Horiz_BluBG.png" alt="UCR Logo">
            </header>
        `;
    }
}

customElements.define('scotty-header', scottyHeader);