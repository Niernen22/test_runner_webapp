let _editingStepId = null;

function showParametersForm() {
    let selectedType = document.getElementById('step_type').value;
    if (selectedType === 'TABLECOPY') {
        document.getElementById('TablecopyForm').style.display = 'block';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    } else if (selectedType === 'LM_JOB') {
        document.getElementById('TablecopyForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'block';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    } else if (selectedType === 'STORED_PROCEDURE') {
        document.getElementById('TablecopyForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'block';
    } else {
        document.getElementById('TablecopyForm').style.display = 'none';
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
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


function getProceduresForSchema(selectedSchema, initialValue = null, onLoaded = null) {
    const storedObjectSelect = window.storedObjectSelectInstance;
    storedObjectSelect.clear();
    storedObjectSelect.clearOptions();

    fetch(SCRIPT_ROOT + '/get_procedures_for_schema?' + new URLSearchParams({ schema: selectedSchema }))
        .then(response => response.json())
        .then(data => {
            data.forEach(procedure => storedObjectSelect.addOption({ value: procedure, text: procedure }));
            storedObjectSelect.refreshOptions(false);
            if (initialValue) {
                storedObjectSelect.addOption({ value: initialValue, text: initialValue });
                storedObjectSelect.setValue(initialValue, true);
                if (onLoaded) onLoaded();
            }
        })
        .catch(error => console.error('Error:', error));
}


function getParametersForStoredProcedure(selectedStoredObjectName, selectedSchema, initialParamValues = {}) {
    fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure?' + new URLSearchParams({ schema: selectedSchema, storedobject_name: selectedStoredObjectName }))
        .then(response => response.json())
        .then(parameterDetails => {
            const parametersDiv = document.getElementById('parameters');
            parametersDiv.innerHTML = '';

            const hasDateParameter = parameterDetails.some(param => param.data_type === 'DATE');
            if (hasDateParameter) {
                fetch(SCRIPT_ROOT + '/get_workdays', { method: 'GET' })
                    .then(response => response.json())
                    .then(workdays => {
                        if (workdays.error) { console.error('Error fetching workdays:', workdays.error); return; }
                        renderParameters(parameterDetails, new Set(workdays), initialParamValues);
                    })
                    .catch(error => console.error('Error fetching workdays:', error));
            } else {
                renderParameters(parameterDetails, null, initialParamValues);
            }
        })
        .catch(error => console.error('Error fetching parameters:', error));
}

function renderParameters(parameterDetails, validDates, initialValues = {}) {
    const parametersDiv = document.getElementById('parameters');
    parameterDetails.forEach(function(parameter) {
        const parameterLabel = document.createElement('label');
        parameterLabel.textContent = parameter.argument_name + ' (' + parameter.in_out + '):';
        parametersDiv.appendChild(parameterLabel);

        if (parameter.in_out === 'IN' || parameter.in_out === 'IN/OUT') {
            const parameterInput = document.createElement('input');
            parameterInput.setAttribute('name', parameter.argument_name);

            if (parameter.data_type === 'DATE') {
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
                parameterInput.value = initialValues[parameter.argument_name] || parameter.default_value || '';
            }
            parametersDiv.appendChild(parameterInput);
        }

        if (parameter.in_out === 'OUT' || parameter.in_out === 'IN/OUT') {
            const outputSpan = document.createElement('span');
            outputSpan.textContent = ' (Output will be displayed after execution)';
            outputSpan.style.fontStyle = 'italic';
            parametersDiv.appendChild(outputSpan);
        }

        parametersDiv.appendChild(document.createElement('br'));
    });
}


function getParametersForStoredProcedureInPackage(selectedStoredObjectName, selectedSchema, selectedPackage, initialParamValues = {}) {
    fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure_in_package?' + new URLSearchParams({ schema: selectedSchema, storedobject_name: selectedStoredObjectName, package_name: selectedPackage }))
        .then(response => response.json())
        .then(parameterDetails => {
            const parametersDiv = document.getElementById('parameters_package');
            parametersDiv.innerHTML = '';

            const hasDateParameter = parameterDetails.some(param => param.data_type === 'DATE');
            if (hasDateParameter) {
                fetch(SCRIPT_ROOT + '/get_workdays', { method: 'GET' })
                    .then(response => response.json())
                    .then(workdays => {
                        if (workdays.error) { console.error('Error fetching workdays:', workdays.error); return; }
                        renderParametersForPackage(parameterDetails, new Set(workdays), initialParamValues);
                    })
                    .catch(error => console.error('Error fetching workdays:', error));
            } else {
                renderParametersForPackage(parameterDetails, null, initialParamValues);
            }
        })
        .catch(error => console.error('Error fetching parameters:', error));
}

function renderParametersForPackage(parameterDetails, validDates, initialValues = {}) {
    const parametersDiv = document.getElementById('parameters_package');
    parameterDetails.forEach(function(parameter) {
        const parameterLabel = document.createElement('label');
        parameterLabel.textContent = parameter.argument_name + ' (' + parameter.in_out + '):';
        parametersDiv.appendChild(parameterLabel);

        if (parameter.in_out === 'IN' || parameter.in_out === 'IN/OUT') {
            const parameterInput = document.createElement('input');
            parameterInput.setAttribute('name', parameter.argument_name);

            if (parameter.data_type === 'DATE') {
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
                parameterInput.value = initialValues[parameter.argument_name] || parameter.default_value || '';
            }
            parametersDiv.appendChild(parameterInput);
        }

        if (parameter.in_out === 'OUT' || parameter.in_out === 'IN/OUT') {
            const outputSpan = document.createElement('span');
            outputSpan.textContent = ' (Output will be displayed after execution)';
            outputSpan.style.fontStyle = 'italic';
            parametersDiv.appendChild(outputSpan);
        }

        parametersDiv.appendChild(document.createElement('br'));
    });
}


function getPackagesForSchema(selectedSchema, initialValue = null, onLoaded = null) {
    fetch(SCRIPT_ROOT + '/get_packages_for_schema?' + new URLSearchParams({ schema: selectedSchema }))
        .then(response => response.json())
        .then(data => {
            const select = window.packageSelectInstance;
            select.clearOptions();
            data.forEach(pkg => select.addOption({ value: pkg, text: pkg }));
            select.refreshOptions(false);
            if (initialValue) {
                select.addOption({ value: initialValue, text: initialValue });
                select.setValue(initialValue, true);
                if (onLoaded) onLoaded();
            }
        })
        .catch(error => console.error('Error:', error));
}

function getProceduresForPackage(selectedPackage, selectedSchema, initialValue = null, onLoaded = null) {
    fetch(SCRIPT_ROOT + '/get_procedures_for_package?' + new URLSearchParams({ schema: selectedSchema, package: selectedPackage }))
        .then(response => response.json())
        .then(data => {
            const select = window.objectInPackageSelectInstance;
            select.clearOptions();
            data.forEach(proc => select.addOption({ value: proc, text: proc }));
            select.refreshOptions(false);
            if (initialValue) {
                select.addOption({ value: initialValue, text: initialValue });
                select.setValue(initialValue, true);
                if (onLoaded) onLoaded();
            }
        })
        .catch(error => console.error('Error:', error));
}


function getTablesForTargetSchema(selectedSchema, initialValue = null) {
    fetch(SCRIPT_ROOT + '/get_tables_for_schema?' + new URLSearchParams({ schema: selectedSchema }))
        .then(response => response.json())
        .then(data => {
            const targetTableSelect = window.targetTableSelectInstance;
            targetTableSelect.clearOptions();
            data.forEach(table => targetTableSelect.addOption({ value: table, text: table }));
            targetTableSelect.refreshOptions(false);
            if (initialValue) {
                targetTableSelect.addOption({ value: initialValue, text: initialValue });
                targetTableSelect.setValue(initialValue, true);
            }
        })
        .catch(error => console.error('Error:', error));
}

function getTablesForTruncateSchema(selectedSchema) {
    const truncateTableSelect = document.getElementById('truncate_table');
    fetch(SCRIPT_ROOT + '/get_tables_for_schema?' + new URLSearchParams({ schema: selectedSchema }))
        .then(response => response.json())
        .then(data => {
            truncateTableSelect.innerHTML = '';
            data.forEach(function(table) {
                const option = document.createElement('option');
                option.value = table;
                option.textContent = table;
                truncateTableSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error:', error));
}


function getTablesForSourceSchema(selectedSchema, initialValue = null) {
    fetch(SCRIPT_ROOT + '/get_tables_for_prod_schema?' + new URLSearchParams({ schema: selectedSchema }))
        .then(response => response.json())
        .then(data => {
            const sourceTableSelect = window.sourceTableSelectInstance;
            sourceTableSelect.clearOptions();
            data.forEach(table => sourceTableSelect.addOption({ value: table, text: table }));
            sourceTableSelect.refreshOptions(false);
            if (initialValue) {
                sourceTableSelect.addOption({ value: initialValue, text: initialValue });
                sourceTableSelect.setValue(initialValue, true);
            }
        })
        .catch(error => console.error('Error:', error));
}


document.addEventListener('DOMContentLoaded', function() {
    fetch(SCRIPT_ROOT + '/get_workdays', { method: 'GET' })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            const dateSelect = document.getElementById('date');
            if (dateSelect) {
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'no-date-selected';
                defaultOption.disabled = true;
                defaultOption.selected = true;
                dateSelect.appendChild(defaultOption);

                const currentDateOption = document.createElement('option');
                currentDateOption.value = 'CURRENT_TND';
                currentDateOption.textContent = 'Current TND';
                dateSelect.appendChild(currentDateOption);

                const maxTndOption = document.createElement('option');
                maxTndOption.value = 'MAX_TND';
                maxTndOption.textContent = 'Max TND';
                dateSelect.appendChild(maxTndOption);

                data.forEach(function(day) {
                    const option = document.createElement('option');
                    option.value = day;
                    option.textContent = day;
                    dateSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error:', error));
});


function getNamesForModule(selectedModule, initialValue = null) {
    fetch(SCRIPT_ROOT + '/get_names_for_module?' + new URLSearchParams({ module: selectedModule }))
        .then(response => response.json())
        .then(data => {
            window.nameSelectInstance.clearOptions();
            data.forEach(name => window.nameSelectInstance.addOption({ value: name, text: name }));
            window.nameSelectInstance.refreshOptions(false);
            if (initialValue) {
                window.nameSelectInstance.addOption({ value: initialValue, text: initialValue });
                window.nameSelectInstance.setValue(initialValue, true);
            }
        })
        .catch(error => console.error('Error:', error));
}


function getTypesForModule(selectedModule, initialValue = null) {
    const typeSpan = document.getElementById('type');
    fetch(SCRIPT_ROOT + '/get_types_for_module?' + new URLSearchParams({ module: selectedModule }))
        .then(response => response.json())
        .then(data => {
            typeSpan.innerHTML = '';
            data.forEach(function(type) {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeSpan.appendChild(option);
            });
            if (initialValue) {
                typeSpan.textContent = initialValue;
            }
        })
        .catch(error => console.error('Error:', error));
}


function openPopup() {
    const modal = document.getElementById('myModal');
    modal.style.display = 'block';

    const span = document.getElementsByClassName('close')[0];

    function closeModal() {
        modal.style.display = 'none';
        _editingStepId = null;
        document.getElementById('modalTitle').textContent = 'Add Step';
    }

    span.onclick = closeModal;
    window.onclick = function(event) {
        if (event.target == modal) closeModal();
    };
}


async function openEditPopup(stepId) {
    const response = await fetch(SCRIPT_ROOT + '/get_step_params/' + stepId);
    if (!response.ok) {
        if (response.status === 404) {
            alert('This step was created before the edit feature was introduced and does not have stored parameters.\n\nTo edit it, please delete it and re-add it — it will be editable from then on.');
        } else {
            alert('Could not load step parameters. Please try again.');
        }
        return;
    }
    const params = await response.json();

    _editingStepId = stepId;
    document.getElementById('modalTitle').textContent = 'Edit Step';
    document.getElementById('new_step_name').value = params.new_step_name || '';
    document.getElementById('step_type').value = params.step_type;
    showParametersForm();
    _prefillForm(params);
    openPopup();
}


function _prefillForm(params) {
    switch (params.step_type) {
        case 'TABLECOPY':
            window.sourceSchemaSelectInstance.setValue(params.source_schema, true);
            getTablesForSourceSchema(params.source_schema, params.source_table);
            window.targetSchemaSelectInstance.setValue(params.target_schema, true);
            getTablesForTargetSchema(params.target_schema, params.target_table);
            document.getElementById('truncate').value = params.truncate;
            document.getElementById('date').value = params.date || '';
            break;

        case 'LM_JOB':
            window.moduleSelectInstance.setValue(params.module, true);
            getTypesForModule(params.module, params.type);
            getNamesForModule(params.module, params.name);
            break;

        case 'STORED_PROCEDURE': {
            document.getElementById('storedprocedure_type').value = params.storedprocedure_type;
            showSPParametersForm();

            const initialParamValues = {};
            (params.parameters || []).forEach(p => { initialParamValues[p.name] = p.value; });

            if (params.storedprocedure_type === 'SingleProcedure') {
                window.procedureSchemaSelectInstance.setValue(params.procedures_schema, true);
                getProceduresForSchema(params.procedures_schema, params.storedobject_name, function() {
                    getParametersForStoredProcedure(params.storedobject_name, params.procedures_schema, initialParamValues);
                });
            } else if (params.storedprocedure_type === 'Package') {
                window.schemaPackageSelectInstance.setValue(params.procedures_schema_package, true);
                getPackagesForSchema(params.procedures_schema_package, params.storedpackage_name, function() {
                    getProceduresForPackage(params.storedpackage_name, params.procedures_schema_package, params.storedobject_name_package, function() {
                        getParametersForStoredProcedureInPackage(params.storedobject_name_package, params.procedures_schema_package, params.storedpackage_name, initialParamValues);
                    });
                });
            }
            break;
        }
    }
}


function submitFormData() {
    let formData = {
        new_step_name: document.getElementById('new_step_name').value.trim(),
        step_type: document.getElementById('step_type').value.trim(),
        source_schema: null, source_table: null,
        target_schema: null, target_table: null,
        truncate: null, date: null,
        module: null, type: null, name: null,
        storedprocedure_type: null,
        procedures_schema: null, storedobject_name: null,
        procedures_schema_package: null, storedpackage_name: null, storedobject_name_package: null,
        parameters: [], parameter_details: []
    };

    if (formData.step_type === 'TABLECOPY') {
        formData.source_schema = document.getElementById('source_schema').value.trim();
        formData.source_table  = document.getElementById('source_table').value.trim();
        formData.target_schema = document.getElementById('target_schema').value.trim();
        formData.target_table  = document.getElementById('target_table').value.trim();
        formData.truncate      = document.getElementById('truncate').value.trim();
        formData.date          = document.getElementById('date').value.trim();
        submitFormDataToServer(formData);

    } else if (formData.step_type === 'TRUNCATE_TABLE') {
        formData.truncate_schema = document.getElementById('truncate_schema').value.trim();
        formData.truncate_table  = document.getElementById('truncate_table').value.trim();
        formData.truncate_date   = document.getElementById('truncate_date').value.trim();
        submitFormDataToServer(formData);

    } else if (formData.step_type === 'LM_JOB') {
        formData.module = document.getElementById('module').value.trim();
        formData.type   = document.getElementById('type').textContent.trim();
        formData.name   = document.getElementById('name').value.trim();
        submitFormDataToServer(formData);

    } else if (formData.step_type === 'STORED_PROCEDURE') {
        formData.storedprocedure_type = document.getElementById('storedprocedure_type').value.trim();

        if (formData.storedprocedure_type === 'SingleProcedure') {
            formData.procedures_schema = document.getElementById('procedures_schema').value.trim();
            formData.storedobject_name = document.getElementById('storedobject_name').value.trim();

            fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure?' + new URLSearchParams({ schema: formData.procedures_schema, storedobject_name: formData.storedobject_name }))
                .then(response => response.json())
                .then(parameterDetails => {
                    formData.parameter_details = parameterDetails;
                    formData.parameters = parameterDetails.map(parameter => ({
                        name: parameter.argument_name,
                        type: parameter.in_out,
                        value: (document.querySelector(`input[name="${parameter.argument_name}"]`) || {}).value?.trim() || null,
                        data_type: parameter.data_type
                    }));
                    submitFormDataToServer(formData);
                })
                .catch(error => {
                    console.error('Error fetching parameter details:', error);
                    alert('There was an error fetching the parameter details.');
                });

        } else if (formData.storedprocedure_type === 'Package') {
            formData.procedures_schema_package  = document.getElementById('procedures_schema_package').value.trim();
            formData.storedpackage_name         = document.getElementById('storedpackage_name').value.trim();
            formData.storedobject_name_package  = document.getElementById('storedobject_name_package').value.trim();

            fetch(SCRIPT_ROOT + '/get_parameters_for_stored_procedure_in_package?' + new URLSearchParams({ schema: formData.procedures_schema_package, storedobject_name: formData.storedobject_name_package, package_name: formData.storedpackage_name }))
                .then(response => response.json())
                .then(parameterDetails => {
                    formData.parameter_details = parameterDetails;
                    formData.parameters = parameterDetails.map(parameter => ({
                        name: parameter.argument_name,
                        type: parameter.in_out,
                        value: (document.querySelector(`input[name="${parameter.argument_name}"]`) || {}).value?.trim() || null
                    }));
                    submitFormDataToServer(formData);
                })
                .catch(error => {
                    console.error('Error fetching parameter details for package:', error);
                    alert('There was an error fetching the parameter details for the package.');
                });
        }
    } else {
        alert('Invalid step type selected.');
    }
}

function submitFormDataToServer(formData) {
    const url = _editingStepId
        ? SCRIPT_ROOT + '/edit_step/' + _editingStepId
        : SCRIPT_ROOT + '/add_step/' + test_id;

    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(_editingStepId ? 'Step successfully updated!' : 'Step successfully added!');
                _editingStepId = null;
                window.location.href = data.redirect_url;
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error during AJAX submission:', error);
            alert('There was an error submitting the form. Please try again.');
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
                window.location.href = SCRIPT_ROOT + `/test_steps/${test_id}`;
            } else {
                alert('Error updating order');
            }
        })
        .catch(error => console.error('Error:', error));
}

document.addEventListener('DOMContentLoaded', enableDragAndDrop);

document.addEventListener('DOMContentLoaded', function () {
    window.moduleSelectInstance = new TomSelect('#module', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        create: false,
        onChange: function(value) {
            getTypesForModule(value);
            getNamesForModule(value);
        }
    });

    window.nameSelectInstance = new TomSelect('#name', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true
    });

    window.sourceSchemaSelectInstance = new TomSelect('#source_schema', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(value) {
            getTablesForSourceSchema(value);
        }
    });

    window.targetSchemaSelectInstance = new TomSelect('#target_schema', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(value) {
            getTablesForTargetSchema(value);
        }
    });

    window.sourceTableSelectInstance = new TomSelect('#source_table', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true
    });

    window.targetTableSelectInstance = new TomSelect('#target_table', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true
    });

    window.procedureSchemaSelectInstance = new TomSelect('#procedures_schema', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(value) {
            getProceduresForSchema(value);
        }
    });

    window.storedObjectSelectInstance = new TomSelect('#storedobject_name', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(value) {
            const selectedSchema = document.getElementById('procedures_schema').value;
            if (value && selectedSchema) {
                getParametersForStoredProcedure(value, selectedSchema);
            }
        }
    });

    window.schemaPackageSelectInstance = new TomSelect('#procedures_schema_package', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(selectedSchema) {
            if (!selectedSchema) return;
            window.packageSelectInstance.clear(true);
            window.objectInPackageSelectInstance.clear(true);
            document.getElementById('parameters_package').innerHTML = '';
            getPackagesForSchema(selectedSchema);
        }
    });

    window.packageSelectInstance = new TomSelect('#storedpackage_name', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(selectedPackage) {
            const selectedSchema = document.getElementById('procedures_schema_package').value;
            if (!selectedPackage || !selectedSchema) return;
            window.objectInPackageSelectInstance.clear(true);
            document.getElementById('parameters_package').innerHTML = '';
            getProceduresForPackage(selectedPackage, selectedSchema);
        }
    });

    window.objectInPackageSelectInstance = new TomSelect('#storedobject_name_package', {
        placeholder: '-- Start typing and select an option --',
        allowEmptyOption: true,
        onChange: function(selectedProcedure) {
            const schema = document.getElementById('procedures_schema_package').value;
            const packageName = document.getElementById('storedpackage_name').value;
            if (!schema || !packageName || !selectedProcedure) return;
            getParametersForStoredProcedureInPackage(selectedProcedure, schema, packageName);
        }
    });
});
