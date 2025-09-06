function myFunction() {
  alert("Hello from a static file!");
}

let consensus = document.getElementById("consensus").innerHTML; 
let result = consensus.replace(/~/g, ",");
document.getElementById("consensus").innerHTML = result;