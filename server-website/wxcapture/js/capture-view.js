function changefilter(filter){
    var pass = "_sample_";
    var newpath = "images/noaa".concat(pass, filter, ".jpg");
    // alert("Test! Filter\nFilter Requested: " + filter + "\nChanging image display source to:\n" + newpath);
    document.getElementById("display").src = newpath;
}