function showParametersForm() {
    let selectedType = document.getElementById('step_type').value;
    if (selectedType === 'TABLECOPY') {
        document.getElementById('parametersForm').style.display = 'block';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    } else if (selectedType === 'LM_JOB') {
        document.getElementById('parametersForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'block';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    } else if (selectedType === 'STORED_PROCEDURE') {
        document.getElementById('parametersForm').style.display = 'none'; 
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'block';
    } else {
        document.getElementById('parametersForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    }
}


function showSPParametersForm() {
    let selectedType = document.getElementById('storedprocedure_type').value;
    if (selectedType === 'Function_or_Procedure') {
        document.getElementById('FunctionOrProcedureForm').style.display = 'block';
        document.getElementById('PackageForm').style.display = 'none';
    } else if (selectedType === 'Package') {
        document.getElementById('FunctionOrProcedureForm').style.display = 'none'; 
        document.getElementById('PackageForm').style.display = 'block';
    } else {
        document.getElementById('FunctionOrProcedureForm').style.display = 'none';
        document.getElementById('PackageForm').style.display = 'none';
    }
}


function getProceduresForSchema(selectedSchema) {
    var storedObjectSelect = document.getElementById('storedobject_name');
    fetch('/get_procedures_for_schema', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ schema: selectedSchema })
    })
    .then(response => response.json())
    .then(data => {
        storedObjectSelect.innerHTML = '';
        data.forEach(function(procedure) {
            var option = document.createElement('option');
            option.value = procedure;
            option.textContent = procedure;
            storedObjectSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getParametersForStoredProcedure(selectedStoredObjectName, selectedSchema) {
    fetch('/get_parameters_for_stored_procedure', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ storedobject_name: selectedStoredObjectName, schema: selectedSchema })
    })
    .then(response => response.json())
    .then(data => {
        var parametersDiv = document.getElementById('parameters');
        parametersDiv.innerHTML = '';
        data.forEach(function(parameter) {
            var parameterLabel = document.createElement('label');
            parameterLabel.textContent = parameter.argument_name + ':';
            parametersDiv.appendChild(parameterLabel);
        
            var parameterInput = document.createElement('input');
            parameterInput.type = 'text';
            parameterInput.value = parameter.default_value;
            parameterInput.setAttribute('name', parameter.argument_name);
            parametersDiv.appendChild(parameterInput);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getParametersForStoredProcedureInPackage(selectedStoredObjectName, selectedSchema, selectedPackage) {
    fetch('/get_parameters_for_stored_procedure_in_package', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ storedobject_name: selectedStoredObjectName, schema: selectedSchema, package_name: selectedPackage })
    })
    .then(response => response.json())
    .then(data => {
        var parametersDiv = document.getElementById('parameters_package');
        parametersDiv.innerHTML = '';
        data.forEach(function(parameter) {
            var parameterLabel = document.createElement('label');
            parameterLabel.textContent = parameter.argument_name + ':';
            parametersDiv.appendChild(parameterLabel);
        
            var parameterInput = document.createElement('input');
            parameterInput.type = 'text';
            parameterInput.value = parameter.default_value;
            parameterInput.setAttribute('name', parameter.argument_name);
            parametersDiv.appendChild(parameterInput);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getPackagesForSchema(selectedSchema) {
    var storedPackageSelect = document.getElementById('storedpackage_name');
    fetch('/get_packages_for_schema', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ schema: selectedSchema })
    })
    .then(response => response.json())
    .then(data => {
        storedPackageSelect.innerHTML = '';
        data.forEach(function(package) {
            var option = document.createElement('option');
            option.value = package;
            option.textContent = package;
            storedPackageSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getProceduresForPackage(selectedPackage, selectedSchema) {
    var storedObjectSelect = document.getElementById('storedobject_name_package');
    fetch('/get_procedures_for_package', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ schema: selectedSchema, package: selectedPackage })
    })
    .then(response => response.json())
    .then(data => {
        storedObjectSelect.innerHTML = '';
        data.forEach(function(procedure) {
            var option = document.createElement('option');
            option.value = procedure;
            option.textContent = procedure;
            storedObjectSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getTablesForTargetSchema(selectedSchema) {
    var targetTableSelect = document.getElementById('target_table');
    fetch('/get_tables_for_schema', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ schema: selectedSchema })
    })
    .then(response => response.json())
    .then(data => {
        targetTableSelect.innerHTML = '';
        data.forEach(function(table) {
            var option = document.createElement('option');
            option.value = table;
            option.textContent = table;
            targetTableSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getTablesForSourceSchema(selectedSchema) {
    var sourceTableSelect = document.getElementById('source_table');
    fetch('/get_tables_for_schema', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ schema: selectedSchema })
    })
    .then(response => response.json())
    .then(data => {
        sourceTableSelect.innerHTML = '';
        data.forEach(function(table) {
            var option = document.createElement('option');
            option.value = table;
            option.textContent = table;
            sourceTableSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_workdays', {
        method: 'GET',
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        var dateSelect = document.getElementById('date');
        data.forEach(function(day) {
            var option = document.createElement('option');
            option.value = day;
            option.textContent = day;
            dateSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
});


function getNamesForModule(selectedModule) {
    var nameSelect = document.getElementById('name');
    fetch('/get_names_for_module', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module: selectedModule })
    })
    .then(response => response.json())
    .then(data => {
        nameSelect.innerHTML = '';
        data.forEach(function(name) {
            var option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            nameSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getTypesForModule(selectedModule) {
    var typeSelect = document.getElementById('type');
    fetch('/get_types_for_module', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module: selectedModule })
    })
    .then(response => response.json())
    .then(data => {
        typeSelect.innerHTML = '';
        data.forEach(function(type) {
            var option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function openPopup() {
    var modal = document.getElementById("myModal");

    modal.style.display = "block";

    var span = document.getElementsByClassName("close")[0];

    span.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
}



function submitFormData() {
    let formData = {
        new_step_name: document.getElementById('new_step_name').value,
        step_type: document.getElementById('step_type').value,
        source_schema: null,
        source_table: null,
        target_schema: null,
        target_table: null,
        truncate: null,
        date: null,
        module: null,
        type: null,
        name: null,
        storedprocedure_type: null,
        procedures_schema: null,
        storedobject_name: null,
        procedures_schema_package: null,
        storedpackage_name: null,
        storedobject_name_package: null,
        parameters: {}
    };
    
    if (formData.step_type === 'TABLECOPY') {
        formData.source_schema = document.getElementById('source_schema').value.trim();
        formData.source_table = document.getElementById('source_table').value.trim();
        formData.target_schema = document.getElementById('target_schema').value.trim();
        formData.target_table = document.getElementById('target_table').value.trim();
        formData.truncate = document.getElementById('truncate').value.trim();
        formData.date = document.getElementById('date').value.trim();
    } else if (formData.step_type === 'LM_JOB') {
        formData.module = document.getElementById('module').value.trim();
        formData.type = document.getElementById('type').textContent.trim();
        formData.name = document.getElementById('name').value.trim();
    } else if (formData.step_type === 'STORED_PROCEDURE') {
        formData.storedprocedure_type = document.getElementById('storedprocedure_type').value.trim();
        if (formData.storedprocedure_type === 'Function_or_Procedure') {
            formData.procedures_schema = document.getElementById('procedures_schema').value.trim();
            formData.storedobject_name = document.getElementById('storedobject_name').value.trim();
            formData.parameters = Array.from(document.getElementById('parameters').getElementsByTagName('input')).reduce((acc, input) => {
                acc[input.name] = input.value.trim();
                return acc;
            }, {});
        } else if (formData.storedprocedure_type === 'Package') {
            formData.procedures_schema_package = document.getElementById('procedures_schema_package').value.trim();
            formData.storedpackage_name = document.getElementById('storedpackage_name').value.trim();
            formData.storedobject_name_package = document.getElementById('storedobject_name_package').value.trim();
            formData.parameters = Array.from(document.getElementById('parameters_package').getElementsByTagName('input')).reduce((acc, input) => {
                acc[input.name] = input.value.trim();
                return acc;
            }, {});
        }
    }

    fetch('/add_step/' + test_id, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Step successfully added!");
            window.location.href = data.redirect_url;
        } else {
            alert("Error: " + data.error);
        }
    })
    .catch(error => {
        console.error('Error during AJAX submission:', error);
        alert("There was an error submitting the form. Please try again.");
    });
}
