document.addEventListener('DOMContentLoaded', function () {
    var confirmPowerActionElement = document.getElementById('confirmPowerAction');
    var manTimeElement = document.getElementById('manTime');
    var queryParams = new URLSearchParams(window.location.search);
    var state = queryParams.get('state');

    if (confirmPowerActionElement) {
        confirmPowerActionElement.style.display = 'none';
    };

    if (manTimeElement) {
        manTimeElement.style.display = 'none';
    };

    if (state === 'welcome' || state === null)  {
        UpdateInformation();
        var intervalID = setInterval(UpdateInformation, 10000);
    } else {
        clearInterval(intervalID);
    }

    function showWelcome() {
        currentstate = 'welcome';
        window.location.href = '/?state=welcome';
    };
   

    function showSetup() {
        currentstate = 'setup';
        window.location.href = '/?state=setup';
    };
    

    function sendData(itemId) {
        var inputData;
        var selectedOption;
        var extraField;
        var executeSend = false;

        if (itemId === 'setupCalcMethod') {
            selectedOption = document.getElementById('SetupCalculationMethod').value;
            extraField = document.getElementById('CalcValueInput').value;
            executeSend = true;
        };

        if (itemId === 'setTime') {
            selectedOption = document.getElementById('SelectTime').value;
            if (selectedOption === 'manual') {
                document.getElementById('manTime').style.display = 'flex';
                executeSend = false
            } else {
                executeSend = true
            }
        };

        if (itemId === 'MoveCords') {
            cord_azim = document.getElementById('manualCordInputAzim').value;
            cord_elev = document.getElementById('manualCordInputElev').value;
            selectedOption = [cord_azim, cord_elev];
            executeSend = true;
        };

        if (itemId === 'testSetup') {
            selectedOption = document.getElementById('SelectedTest').value;
            executeSend = true;
        };

        if (itemId === 'SelectedPowerOperation') {
            selectedOption = document.getElementById('Power').value;
            document.getElementById('confirmPowerAction').style.display = 'block';
        };

        if (itemId === 'confirmPowerAction') {
            extraField = 'confirmed';
            selectedOption = document.getElementById('Power').value;
            executeSend = true;
        };

        if (itemId === 'setLocation') {
            selectedOption = document.getElementById('location').value;
            executeSend = true;
        };

        if (itemId === 'manTime') {
            selectedOption = 'manual';
            extraField = document.getElementById('manualTimeInput').value;
            executeSend = true;
        };



        if (executeSend) {
            var dataToSend = {
                itemId: itemId,
                selectedOption: selectedOption,
                extraField: extraField
            };

            fetch('/process_setup_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dataToSend)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Response from Flask:', data);
                window.location.href = '/?state=setup';
            })
            .catch(error => console.error('Error:', error));
        };
    };

    window.showSetup = showSetup;
    window.showWelcome = showWelcome;
    window.sendData = sendData;
    
});

async function fetch_information() {
    return fetch('/get_information')
        .then(response => response.json())
        .then(data => {
            return {
                online_since: data.online_since,
                device: data.device,
                status: data.status,
                timezone: data.timezone,
                time_source: data.time_source,
                calculation_method: data.calculation_method,
                calculation_value: data.calculation_value,
                location: data.location,
                elevation: data.elevation,
                azimuth: data.azimuth,
                last_calculation: data.last_calculation,
                man_time: data.man_time
            };
        })
        .catch(error => {
            console.error('Error:', error);
            throw error; // Rethrow the error to propagate it further if needed
        });
}




async function UpdateInformation() {
    var jsonData;    
    try {
        jsonData = await fetch_information();
        
        document.querySelector('.system-information').innerHTML = `
            <br> Online since: ${jsonData.online_since}
            <br> Device: ${jsonData.device}
            <br> Status: ${jsonData.status}
            <br> Timezone: ${jsonData.timezone}
            <br> Source: ${jsonData.time_source}
            <br> Calculation_method: ${jsonData.calculation_method}
            <br> Value: ${jsonData.calculation_value}
            <br> Location: ${jsonData.location}
            <br> Manual Time: ${jsonData.man_time}
        `;
        document.querySelector('.sunstatus').innerHTML = `
            <br> Elevation: ${jsonData.elevation}
            <br> Azimuth: ${jsonData.azimuth}
            <br> Last Calculation: ${jsonData.last_calculation}
            `;
        
} catch (error) {
    console.error('Error:', error);
}};

function closeSetupItem(imgElement) {
    var setupItem = imgElement.closest('.setupitem');

    if (setupItem) {
        setupItem.style.display = 'none';
    }
}

function resetSetupItems() {
    var setupItems = document.querySelectorAll('.setupitem');
    var confirmPowerActionElement = document.getElementById('confirmPowerAction');
    var manTimeElement = document.getElementById('manTime');

    setupItems.forEach(function (item) {
        item.style.display = 'flex';
    });
    
    if (confirmPowerActionElement) {
        confirmPowerActionElement.style.display = 'none';
    };

    if (manTimeElement) {
        manTimeElement.style.display = 'none';
    };
}


