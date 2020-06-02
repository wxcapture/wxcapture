function changefilter(filter){
    var pass = "2020-06-01-21-35-48-NOAA_18";
    var path = "images/noaa".concat(pass, "-", filter, ".jpg");
    alert("Test! Filter\nFilter Requested: " + filter + "\nChanging image display source to:\n" + newpath);
    document.getElementById("display").src = path;
    document.getElementById("description").innerHTML = about_filter(filter);
}

// za, no, mcir-precip, mcir, therm, sea, contrasta, contrastb

function about_filter(filter){
    switch(filter){
        case "za":
            return "Enhanced infra red image";
        case "no":
            return "No colour infrared enhanced image";
        case "mcir-precip":
            return "Coloured infrared image highlighting precipitation";
        case "mcir":
            return "Coloured infrared image";
        case "therm":
            return "Air temperature image";
        case "sea":
            return "Sea surface temperature image";
        case "contrasta":
            return "Contrast - Channel A image";
        case "contrastb":
            return "Contrast - Channel B image";
        
        default:
            return "Filter not found. Please submit an issue on GitHub for Albert (technobird22)";
    }
}