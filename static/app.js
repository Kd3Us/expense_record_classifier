const fileInput = document.getElementById("file-input");
const imagePreview = document.getElementById("image-preview");
const dropZone = document.getElementById("drop-zone");
const dropLabel = document.getElementById("drop-label");

let currentFile = null;

function handleFile(file) {
    if (!file) return;
    currentFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreview.classList.add("visible");
        dropLabel.textContent = file.name.toUpperCase();
    };
    reader.readAsDataURL(file);
}

dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => handleFile(e.target.files[0]));

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (!file) return;

    // Injecte le fichier droppé dans le vrai input pour qu'HTMX le sérialise correctement
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;

    handleFile(file);
});

// HTMX ne swap pas sur les 4xx/5xx par défaut (pour le formulaire de submit)
document.addEventListener("htmx:responseError", (e) => {
    if (e.detail.target) e.detail.target.innerHTML = e.detail.xhr.responseText;
});

window.resetApp = function () {
    document.getElementById("form-container").innerHTML = "";
    document.getElementById("confirmation-container").innerHTML = "";
    imagePreview.classList.remove("visible");
    imagePreview.src = "";
    fileInput.value = "";
    dropLabel.textContent = "DROP ZONE — CLIQUER OU GLISSER";
    currentFile = null;
};
