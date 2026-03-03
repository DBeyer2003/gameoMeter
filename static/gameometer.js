//Used to hide and unhide the score chart info/links.
function showDateInfo() {
  var x = document.getElementById("chartReviews");
  var dateButton = document.getElementById("dateButton");
  if (x.style.display === "none") {
    x.style.display = "block";
    tcButton.style.display = "block";
    dateButton.textContent = "Hide Dates";
  } else {
    x.style.display = "none";
    dateButton.textContent = "Show Dates";
  }
}

//Used to toggle between top critic and all critic info on 
//score info page.
function showTCInfo() {
  var ac_info = document.getElementById("all-chart");
  var tc_info = document.getElementById("top-chart");
  var toggleButton = document.getElementById("TCButton");
  
  if (ac_info.style.display === "inline"){
    ac_info.style.display = "none";
    tc_info.style.display = "inline";
    toggleButton.textContent = "Show All Reviews";
  } else {
    ac_info.style.display = "inline";
    tc_info.style.display = "none";
    toggleButton.textContent = "Show Top Reviews";
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

// Used to toggle between top critics and all critics.
function toggleCritics() {
  var all_c = document.getElementById("all-critics-info");
  var top_c = document.getElementById("top-critics-info");
  var tc_button = document.getElementById("show-top-critics");
  if (all_c.style.display == "flex") {
    all_c.style.display = "none";
    top_c.style.display = "flex";
    tc_button.textContent = "Show All Critics"; 
  } else {
    all_c.style.display = "flex";
    top_c.style.display = "none";
    tc_button.textContent = "Show Top Critics"; 
  }
}

//Used to display the console/date filters for a game when 
//the button is clicked.
function toggleFilters() {
  var filter_box = document.getElementById("show-filters");
  if (filter_box.style.display == "none") {
    filter_box.style.display = "block";
  }else {
    filter_box.style.display = "none";
  }
}

let consensus = document.getElementById("consensus").innerHTML; 
let result = consensus.replaceAll(/~/g, ",");
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

  let consensus = document.getElementById("consensus").innerHTML; 
  let result = consensus.replaceAll(/~/g, ",");
  document.getElementById("consensus").innerHTML = result;

  document.querySelectorAll("consensus").forEach(element => {
    element.style.color = 'green';
  })

}