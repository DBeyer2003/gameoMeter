function showDateInfo() {
  var x = document.getElementById("chartReviews");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}

let consensus = document.getElementById("consensus").innerHTML; 
let result = consensus.replace(/~/g, ",");
document.getElementById("consensus").innerHTML = result;