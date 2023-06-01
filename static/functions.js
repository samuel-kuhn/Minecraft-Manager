function confirmReset() {
    confirm("Do you really want to reset the world? \nEvery progress will be deleted!");
}

function confirmRemove() {
    confirm("Do you really want to delete this Server?");
}

function toggleInputField() {
    var inputField = document.getElementById("hiddenInput");
    var submitButton = document.getElementById("hiddenButton");
    inputField.classList.toggle("hidden");
    submitButton.classList.toggle("hidden");
  }
  