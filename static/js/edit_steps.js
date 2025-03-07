function showParametersForm() {
    let selectedType = document.getElementById('step_type').value;
    if (selectedType === 'TABLECOPY') {
        document.getElementById('TablecopyForm').style.display = 'block';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
        //document.getElementById('TruncateForm').style.display = 'none';
    } else if (selectedType === 'LM_JOB') {
        document.getElementById('TablecopyForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'block';
        document.getElementById('StoredProcedureForm').style.display = 'none';
        //document.getElementById('TruncateForm').style.display = 'none';
    //} else if (selectedType === 'TRUNCATE_TABLE') {
        //document.getElementById('TablecopyForm').style.display = 'none';
        //document.getElementById('LMparametersForm').style.display = 'none';
        //document.getElementById('StoredProcedureForm').style.display = 'none';
        //document.getElementById('TruncateForm').style.display = 'block';
    } else if (selectedType === 'STORED_PROCEDURE') {
        document.getElementById('TablecopyForm').style.display = 'none'; 
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'block';
        //document.getElementById('TruncateForm').style.display = 'none';
    } else {
        document.getElementById('TablecopyForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
        //document.getElementById('TruncateForm').style.display = 'none';
    }
}


function showSPParametersForm() {
    let selectedType = document.getElementById('storedprocedure_type').value;
    if (selectedType === 'SingleProcedure') {
        document.getElementById('ProcedureForm').style.display = 'block';
        document.getElementById('PackageForm').style.display = 'none';
    } else if (selectedType === 'Package') {
        document.getElementById('ProcedureForm').style.display = 'none'; 
        document.getElementById('PackageForm').style.display = 'block';
    } else {
        document.getElementById('ProcedureForm').style.display = 'none';
        document.getElementById('PackageForm').style.display = 'none';
    }
}


function getProceduresForSchema(selectedSchema) {
    var storedObjectSelect = document.getElementById('storedobject_name');
    fetch(SCRIPT_ROOT + '/get_procedures_for_schema', {
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
    fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ storedobject_name: selectedStoredObjectName, schema: selectedSchema })
    })
    .then(response => response.json())
    .then(parameterDetails => {
        var parametersDiv = document.getElementById('parameters');
        parametersDiv.innerHTML = ''; 

        let hasDateParameter = parameterDetails.some(param => param.data_type === "DATE");

        if (hasDateParameter) {
            fetch(SCRIPT_ROOT + '/get_workdays', { method: 'GET' })
            .then(response => response.json())
            .then(workdays => {
                if (workdays.error) {
                    console.error('Error fetching workdays:', workdays.error);
                    return;
                }

                renderParameters(parameterDetails, new Set(workdays));
            })
            .catch(error => console.error('Error fetching workdays:', error));
        } else {
            renderParameters(parameterDetails, null);
        }
    })
    .catch(error => console.error('Error fetching parameters:', error));
}

function renderParameters(parameterDetails, validDates) {
    var parametersDiv = document.getElementById('parameters');
    parameterDetails.forEach(function(parameter) {
        var parameterLabel = document.createElement('label');
        parameterLabel.textContent = parameter.argument_name + ' (' + parameter.in_out + '):';
        parametersDiv.appendChild(parameterLabel);

        if (parameter.in_out === 'IN' || parameter.in_out === 'IN/OUT') {
            var parameterInput = document.createElement('input');
            parameterInput.setAttribute('name', parameter.argument_name);

            if (parameter.data_type === "DATE") {
                parameterInput.type = 'text';
                parameterInput.classList.add('date-picker');

                setTimeout(() => {
                    $(parameterInput).datepicker({
                        dateFormat: 'yy-mm-dd',
                        beforeShowDay: function(date) {
                            let formattedDate = $.datepicker.formatDate('yy-mm-dd', date);
                            return [validDates ? validDates.has(formattedDate) : true];
                        }
                    });
                }, 0);
            } else {
                parameterInput.type = 'text';
                parameterInput.value = parameter.default_value || ''; 
            }

            parametersDiv.appendChild(parameterInput);
        } 

        if (parameter.in_out === 'OUT' || parameter.in_out === 'IN/OUT') {
            var outputSpan = document.createElement('span');
            outputSpan.textContent = ' (Output will be displayed after execution)';
            outputSpan.style.fontStyle = 'italic';
            parametersDiv.appendChild(outputSpan);
        }

        parametersDiv.appendChild(document.createElement('br'));
    });
}



function getParametersForStoredProcedureInPackage(selectedStoredObjectName, selectedSchema, selectedPackage) {
    fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure_in_package', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ storedobject_name: selectedStoredObjectName, schema: selectedSchema, package_name: selectedPackage })
    })
    .then(response => response.json())
    .then(parameterDetails => {
        var parametersDiv = document.getElementById('parameters_package');
        parametersDiv.innerHTML = '';

        let hasDateParameter = parameterDetails.some(param => param.data_type === "DATE");

        if (hasDateParameter) {
            fetch(SCRIPT_ROOT + '/get_workdays', { method: 'GET' })
            .then(response => response.json())
            .then(workdays => {
                if (workdays.error) {
                    console.error('Error fetching workdays:', workdays.error);
                    return;
                }

                renderParametersForPackage(parameterDetails, new Set(workdays));
            })
            .catch(error => console.error('Error fetching workdays:', error));
        } else {
            renderParametersForPackage(parameterDetails, null);
        }
    })
    .catch(error => console.error('Error fetching parameters:', error));
}

function renderParametersForPackage(parameterDetails, validDates) {
    var parametersDiv = document.getElementById('parameters_package');
    parameterDetails.forEach(function(parameter) {
        var parameterLabel = document.createElement('label');
        parameterLabel.textContent = parameter.argument_name + ' (' + parameter.in_out + '):';
        parametersDiv.appendChild(parameterLabel);

        if (parameter.in_out === 'IN' || parameter.in_out === 'IN/OUT') {
            var parameterInput = document.createElement('input');
            parameterInput.setAttribute('name', parameter.argument_name);

            if (parameter.data_type === "DATE") {
                parameterInput.type = 'text';
                parameterInput.classList.add('date-picker');

                setTimeout(() => {
                    $(parameterInput).datepicker({
                        dateFormat: 'yy-mm-dd',
                        beforeShowDay: function(date) {
                            let formattedDate = $.datepicker.formatDate('yy-mm-dd', date);
                            return [validDates ? validDates.has(formattedDate) : true];
                        }
                    });
                }, 0);
            } else {
                parameterInput.type = 'text';
                parameterInput.value = parameter.default_value || ''; 
            }

            parametersDiv.appendChild(parameterInput);
        } 

        if (parameter.in_out === 'OUT' || parameter.in_out === 'IN/OUT') {
            var outputSpan = document.createElement('span');
            outputSpan.textContent = ' (Output will be displayed after execution)';
            outputSpan.style.fontStyle = 'italic';
            parametersDiv.appendChild(outputSpan);
        }

        parametersDiv.appendChild(document.createElement('br'));
    });
}


function getPackagesForSchema(selectedSchema) {
    var storedPackageSelect = document.getElementById('storedpackage_name');
    fetch(SCRIPT_ROOT + '/get_packages_for_schema', {
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
    fetch(SCRIPT_ROOT + '/get_procedures_for_package', {
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
    fetch(SCRIPT_ROOT + '/get_tables_for_schema', {
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

function getTablesForTruncateSchema(selectedSchema) {
    var truncateTableSelect = document.getElementById('truncate_table');
    fetch(SCRIPT_ROOT + '/get_tables_for_schema', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ schema: selectedSchema })
    })
    .then(response => response.json())
    .then(data => {
        truncateTableSelect.innerHTML = '';
        data.forEach(function(table) {
            var option = document.createElement('option');
            option.value = table;
            option.textContent = table;
            truncateTableSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}


function getTablesForSourceSchema(selectedSchema) {
    var sourceTableSelect = document.getElementById('source_table');
    fetch(SCRIPT_ROOT + '/get_tables_for_prod_schema', {
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
    fetch(SCRIPT_ROOT + '/get_workdays', {
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
        if (dateSelect) {
            var defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.textContent = "no-date-selected";
            defaultOption.disabled = true;
            defaultOption.selected = true;
            dateSelect.appendChild(defaultOption);

            data.forEach(function(day) {
                var option = document.createElement('option');
                option.value = day;
                option.textContent = day;
                dateSelect.appendChild(option);
            });
        }

        var truncateDateSelect = document.getElementById('truncate_date');
        if (truncateDateSelect) {
            truncateDateSelect.innerHTML = '';

            var defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.textContent = "no-date-selected";
            defaultOption.selected = true;
            truncateDateSelect.appendChild(defaultOption);

            data.forEach(function(day) {
                var option = document.createElement('option');
                option.value = day;
                option.textContent = day;
                truncateDateSelect.appendChild(option);
            });

            let validDates = new Set(data);
            $('#truncate_date').datepicker({
                dateFormat: 'yy-mm-dd',
                beforeShowDay: function(date) {
                    let formattedDate = $.datepicker.formatDate('yy-mm-dd', date);
                    return [validDates.has(formattedDate)];
                },
                onSelect: function(selectedDate) {
                    truncateDateSelect.value = selectedDate;
                }
            });

            truncateDateSelect.addEventListener('change', function() {
                $('#truncate_date').datepicker('setDate', this.value || null);
            });
        }
    })
    .catch(error => console.error('Error:', error));
});



function getNamesForModule(selectedModule) {
    var nameSelect = document.getElementById('name');
    fetch(SCRIPT_ROOT + '/get_names_for_module', {
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
    fetch(SCRIPT_ROOT + '/get_types_for_module', {
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
        new_step_name: document.getElementById('new_step_name').value.trim(),
        step_type: document.getElementById('step_type').value.trim(),
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
        parameters: [],
        parameter_details: [] // Add this to include parameter details
    };

    if (formData.step_type === 'TABLECOPY') {
        formData.source_schema = document.getElementById('source_schema').value.trim();
        formData.source_table = document.getElementById('source_table').value.trim();
        formData.target_schema = document.getElementById('target_schema').value.trim();
        formData.target_table = document.getElementById('target_table').value.trim();
        formData.truncate = document.getElementById('truncate').value.trim();
        formData.date = document.getElementById('date').value.trim();
        submitFormDataToServer(formData);

    } else if (formData.step_type === 'TRUNCATE_TABLE') {
        formData.truncate_schema = document.getElementById('truncate_schema').value.trim();
        formData.truncate_table = document.getElementById('truncate_table').value.trim();
        formData.truncate_date = document.getElementById('truncate_date').value.trim();
        submitFormDataToServer(formData);

    } else if (formData.step_type === 'LM_JOB') {
        formData.module = document.getElementById('module').value.trim();
        formData.type = document.getElementById('type').textContent.trim();
        formData.name = document.getElementById('name').value.trim();
        submitFormDataToServer(formData);

    } else if (formData.step_type === 'STORED_PROCEDURE') {
        formData.storedprocedure_type = document.getElementById('storedprocedure_type').value.trim();

        if (formData.storedprocedure_type === 'SingleProcedure') {
            formData.procedures_schema = document.getElementById('procedures_schema').value.trim();
            formData.storedobject_name = document.getElementById('storedobject_name').value.trim();

            fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    schema: formData.procedures_schema,
                    storedobject_name: formData.storedobject_name
                })
            })
            .then(response => response.json())
            .then(parameterDetails => {
                formData.parameter_details = parameterDetails;
                formData.parameters = parameterDetails.map(parameter => {
                    let paramName = parameter.argument_name;
                    let paramType = parameter.in_out;

                    let paramInput = document.querySelector(`input[name="${paramName}"]`);
                    let paramValue = paramInput ? paramInput.value.trim() : null;

                    return {
                        name: paramName,
                        type: paramType,
                        value: paramValue
                    };
                });

                submitFormDataToServer(formData);
            })
            .catch(error => {
                console.error('Error fetching parameter details:', error);
                alert("There was an error fetching the parameter details.");
            });

        } else if (formData.storedprocedure_type === 'Package') {
            formData.procedures_schema_package = document.getElementById('procedures_schema_package').value.trim();
            formData.storedpackage_name = document.getElementById('storedpackage_name').value.trim();
            formData.storedobject_name_package = document.getElementById('storedobject_name_package').value.trim();

            fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure_in_package', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    schema: formData.procedures_schema_package,
                    storedobject_name: formData.storedobject_name_package,
                    package_name: formData.storedpackage_name
                })
            })
            .then(response => response.json())
            .then(parameterDetails => {
                formData.parameter_details = parameterDetails;
                formData.parameters = parameterDetails.map(parameter => {
                    let paramName = parameter.argument_name;
                    let paramType = parameter.in_out;

                    let paramInput = document.querySelector(`input[name="${paramName}"]`);
                    let paramValue = paramInput ? paramInput.value.trim() : null;

                    return {
                        name: paramName,
                        type: paramType,
                        value: paramValue
                    };
                });

                submitFormDataToServer(formData);
            })
            .catch(error => {
                console.error('Error fetching parameter details for package:', error);
                alert("There was an error fetching the parameter details for the package.");
            });
        }
    } else {
        alert("Invalid step type selected.");
    }
}

function submitFormDataToServer(formData) {
    fetch(SCRIPT_ROOT + '/add_step/' + test_id, {
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




function enableDragAndDrop() {
    const rows = document.querySelectorAll('tbody tr');
    let draggingRow = null;

    rows.forEach(row => {
        row.draggable = true;

        row.addEventListener('dragstart', (event) => {
            draggingRow = row;
            row.classList.add('dragging');
            event.dataTransfer.setData('text/plain', row.rowIndex);
        });

        row.addEventListener('dragover', (event) => {
            event.preventDefault();
            const currentRow = event.target.closest('tr');

            if (draggingRow && draggingRow !== currentRow) {
                currentRow.classList.add('drop-target');
            }
        });

        row.addEventListener('dragleave', () => {
            row.classList.remove('drop-target');
        });

        row.addEventListener('drop', (event) => {
            event.preventDefault();
            const currentRow = event.target.closest('tr');

            if (draggingRow && draggingRow !== currentRow) {
                const tbody = document.querySelector('tbody');

                if (draggingRow.rowIndex < currentRow.rowIndex) {
                    tbody.insertBefore(draggingRow, currentRow.nextSibling);
                } else {
                    tbody.insertBefore(draggingRow, currentRow);
                }

                draggingRow.classList.remove('moving-up', 'moving-down', 'dragging');
                currentRow.classList.remove('drop-target');
            }

            draggingRow = null;
        });

        row.addEventListener('dragend', () => {
            row.classList.remove('dragging', 'moving-up', 'moving-down');
        });
    });
}



function finishEditing() {
    const rows = document.querySelectorAll('tbody tr');
    const data = [];

    rows.forEach((row, index) => {
        const id = row.querySelector('input[name="id"]').value;
        data.push({ id: id, order_number: index + 1 });
    });

    fetch(SCRIPT_ROOT + '/update_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href =SCRIPT_ROOT + `/test_steps/${test_id}`;
        } else {
            alert('Error updating order');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

document.addEventListener('DOMContentLoaded', enableDragAndDrop);
