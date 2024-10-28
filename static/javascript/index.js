// Functions for dropdowns

function toggleDropdown(dropdownId) {
    var dropdown = document.getElementById(dropdownId);
    if (dropdown.style.display === 'block') {
        dropdown.style.display = 'none';
    } else { // Close all other dropdowns and then make this one appear
        closeAllDropdowns();
        dropdown.style.display = 'block';
    }
}

// closes all dropdowns
function closeAllDropdowns() {
    closeDropdown('dropdown1');
    closeDropdown('dropdown2');
    closeDropdown('dropdown3');
    // Add more dropdown IDs here if needed
}

// closes a single dropdown
function closeDropdown(dropdownId) {
    var dropdown = document.getElementById(dropdownId);
    dropdown.style.display = 'none';
}

// Functions to copy dropdown lists into the search input

// copies gene into search bar
function copyGeneToInput(){
    var sel = document.getElementById("geneSelections");
    var val = sel.options[sel.selectedIndex].value;
    document.getElementById("searchInput").value = val;
}

// copies mesh into search bar
function copyMeshToInput(){
    var sel = document.getElementById("meshSelections");
    var val = sel.options[sel.selectedIndex].value;
    document.getElementById("meshInput").value = val;
}

// copies multiple genes into search bar and formats them properly
function copyMultipleGenesToInput(){
    var sel = document.getElementById("multipleGeneSelections");
    var val = sel.options[sel.selectedIndex].value;
    var userInput = document.getElementById("multiGeneInput");
    if (userInput.value == ""){
        userInput.value = val;
    } else {
        userInput.value += ',' + val;
    }
}