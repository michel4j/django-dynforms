// heavily inspired by https://auct.github.io/b5toast
var dfToasts = {
    createToastElement: function (html) {
        const template = document.createElement("template");
        html = html.trim();
        template.innerHTML = html;
        return template.content.firstChild;
    },
    show: function (params) {
        let dfToastContainer = document.getElementById("toast-container");
        if (!dfToastContainer) {
            dfToastContainer = document.createElement("div");
            dfToastContainer.id = "toast-container";
            dfToastContainer.className = "position-fixed bottom-0 end-0 p-3";
            document.body.appendChild(dfToastContainer);
        }
        let defaults = {
            theme: "light",     // default theme, can be "light" or "dark"
            color: "light",     // default background color, can be "light", "primary", "secondary", etc
            title: "",          // optional title
            message: "This is a toast message", // default message
            delay: 3000,        // default delay in milliseconds
            textColor: ""       // text-color, will be appended to "text-" to create a class like "text-white"
        };
        let options = Object.assign({}, defaults, params);
        let title = "";
        let closeBtn = '<button type="button" class="btn-close ms-auto me-1" data-bs-dismiss="toast" aria-label="Close"></button>';
        if (options.title) {
            title = `
                <div class="toast-header d-flex flex-row bg-transparent text-${options.textColor}">
                <strong>${options.title}</strong>${closeBtn}</div>
            `;
            closeBtn = ""; // if title is set, we don't need the close button in the body
        }
        const html = `
        <div data-bs-theme="${options.theme}" 
            class="toast d-flex flex-column align-items-stretch mt-1 text-${options.textColor} bg-${options.color} border-0" role="alert" 
            aria-live="assertive" aria-atomic="true">
            ${title}
            <div class="toast-body d-flex">
                <div>${options.message}</div>${closeBtn}
            </div>
        </div>`;
        const toastElement = dfToasts.createToastElement(html);
        dfToastContainer.appendChild(toastElement);
        const toast = new bootstrap.Toast(toastElement, {
            delay: options.delay, animation: true
        });
        toast.show();
        setTimeout(() => toastElement.remove(), options.delay + 1000); // + 1 second for animation
    },
    error: function (parameters) {
        let options = Object.assign({'theme': 'dark', 'color': 'danger', 'textColor': 'white'}, parameters);
        dfToasts.show(options);
    },
    success: function (parameters) {
        let options = Object.assign({'theme': 'dark', 'color': 'success', 'textColor': 'white'}, parameters);
        dfToasts.show(options);
    },
    info: function (parameters) {
        let options = Object.assign({'theme': 'dark', 'color': 'info', 'textColor': 'white'}, parameters);
        dfToasts.show(options);
    },
    warning: function (parameters) {
        let options = Object.assign({'theme': 'dark', 'color': 'warning', 'textColor': 'white'}, parameters);
        dfToasts.show(options);
    }
};