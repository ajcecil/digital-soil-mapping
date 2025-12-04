# Iowa State Agronomy Farm Soil Mapping

Map Documentation

## Contents

- [Datastore](https://iastate.app.box.com/folder/330408802946?s=ytjl7nqkroxs3haodak27xjpkaqpajh4)


# Map Data
## My Leaflet Map

<div id="map" style="height: 400px;"></div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
  document.addEventListener("DOMContentLoaded", function () {
    var map = L.map('map').setView([39.8283, -98.5795], 4); // Center on USA

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
  });
</script>



## Soil Properties

### pH

### Base pH

### Organic Matter 

### Phosphorus (Melich 3)

### Potassium

### Sulfur

### Cation Exchange Capacity

### Calcium

### Magnesium

### H_SAT

### K_SAT

### MG_SAT

### CA_SAT
