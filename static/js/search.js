function liveSearch() {
    let query = document.getElementById('search').value;
    if (query.length > 0) {
        fetch(`/search?query=${query}`)
            .then(response => response.json())
            .then(data => {
                let resultsContainer = document.getElementById('results-container');
                resultsContainer.innerHTML = ''; // Clear previous results
                if (data.results.length > 0) {
                    let resultsList = document.createElement('ul');
                    data.results.forEach(result => {
                        let listItem = document.createElement('li');
                        let link = document.createElement('a');
                        link.href = `/person/${result[0]}`;
                        link.textContent = `${result[1]} ${result[2]} (ur. ${result[3]})`;
                        listItem.appendChild(link);
                        resultsList.appendChild(listItem);
                    });
                    resultsContainer.appendChild(resultsList);
                }
            });
    } else {
        document.getElementById('results-container').innerHTML = ''; // Clear results if query is empty
    }
}

 function redirectTo(url) {
        window.location.href = url;
}
