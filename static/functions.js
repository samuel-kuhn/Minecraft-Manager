function confirmReset() {
    confirm("Do you really want to reset the world? \nEvery progress will be deleted!");
}

function confirmRemove() {
    confirm("Do you really want to delete this Server?");
}

function toggleHidden(elementId) {
  var x = document.getElementById(elementId);
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
} 