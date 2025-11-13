function showDateInfo() {
  var x = document.getElementById("chartReviews");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}


function showFilterInfo() {
  var x = document.getElementById("chartReviews");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}

function toggleCritics() {
  var all_c = document.getElementById("all-critics-info");
  var top_c = document.getElementById("top-critics-info");
  if (all_c.style.display == "flex") {
    all_c.style.display = "none";
    top_c.style.display = "flex";
  } else {
    all_c.style.display = "flex";
    top_c.style.display = "none";
  }
}

let consensus = document.getElementById("consensus").innerHTML; 
let result = consensus.replace(/~/g, ",");
document.getElementById("consensus").innerHTML = result;

// Immediately display results when searching for games.
function instantSearch() {
  var input = document.getElementById('gameSearch');
  var ul = document.getElementById("gameSearch");
  var li = ul.getElementsByTagName('li');
  

  for (n = 0; n < li.length; n++){
    print(li[n])
  }

}

// Test function.
function myFunction() { 
  var input = document.getElementById('gameSearch');
  var ul = document.getElementById("searchResults");
  var li = ul.getElementsByTagName('li');
  

  for (n = 0; n < li.length; n++){
    li[n].style.display = "none";
  }
}