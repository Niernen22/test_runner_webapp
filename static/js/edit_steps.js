function showParametersForm() {
    let selectedType = document.getElementById('step_type').value;
    if (selectedType === 'TABLECOPY') {
        document.getElementById('parametersForm').style.display = 'block';
        document.getElementById('generateSQLButton').style.display = 'inline-block'; 
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    } else if (selectedType === 'LM_JOB') {
        document.getElementById('parametersForm').style.display = 'none';
        document.getElementById('generateSQLButton').style.display = 'inline-block'; 
        document.getElementById('LMparametersForm').style.display = 'block';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    } else if (selectedType === 'STORED_PROCEDURE') {
        document.getElementById('parametersForm').style.display = 'none';
        document.getElementById('generateSQLButton').style.display = 'none'; 
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'block';
    } else {
        document.getElementById('parametersForm').style.display = 'none';
        document.getElementById('generateSQLButton').style.display = 'none'; 
        document.getElementById('LMparametersForm').style.display = 'none';
        document.getElementById('StoredProcedureForm').style.display = 'none';
    }
}


function showSPParametersForm() {
    let selectedType = document.getElementById('storedprocedure_type').value;
    if (selectedType === 'Function_or_Procedure') {
        document.getElementById('FunctionOrProcedureForm').style.display = 'block';
        document.getElementById('generateSQLButtonSP').style.display = 'inline-block'; 
        document.getElementById('PackageForm').style.display = 'none';
    } else if (selectedType === 'Package') {
        document.getElementById('FunctionOrProcedureForm').style.display = 'none';
        document.getElementById('generateSQLButtonSP').style.display = 'inline-block'; 
        document.getElementById('PackageForm').style.display = 'block';
    } else {
        document.getElementById('FunctionOrProcedureForm').style.display = 'none';
        document.getElementById('generateSQLButtonSP').style.display = 'none'; 
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


function generateSQL() {
    var selectedType = document.getElementById('step_type').value;
    if (selectedType === 'TABLECOPY') {
        var sourceSchema = document.getElementById('source_schema').value;
        var sourceTable = document.getElementById('source_table').value;
        var targetSchema = document.getElementById('target_schema').value;
        var targetTable = document.getElementById('target_table').value;
        var truncate = document.getElementById('truncate').value;
        var chosenDate = document.getElementById('date').value;
        
        var sqlCode = "BEGIN ";
        sqlCode += "TABLECOPY_PACKAGE.TABLECOPY(";
        sqlCode += "'" + sourceSchema + "', ";
        sqlCode += "'" + sourceTable + "', ";
        sqlCode += "'" + targetSchema + "', ";
        sqlCode += "'" + targetTable + "', ";
        sqlCode += "'" + truncate + "', ";
        sqlCode += "TO_DATE('" + chosenDate + "','yyyy-mm-dd')); END;";
        
        return sqlCode;

    } else if (selectedType === 'LM_JOB') {
        var type = document.getElementById('type').value;
        var module = document.getElementById('module').value;
        var name = document.getElementById('name').value;
        
        console.log("LM_JOB parameters:", { type, module, name });

        var sqlCode = "declare ";
        sqlCode += "p_result varchar2(4000); ";
        sqlCode += "p_err_code varchar2(4000); ";
        sqlCode += "p_output clob; ";
        sqlCode += "begin ";
        sqlCode += "lm." + type + ".execute(1, '" + module + "', '" + name + "', p_result, p_err_code, p_output, false); ";
        sqlCode += "dbms_output.put_line(p_result || ' - ' || p_err_code); ";
        sqlCode += "dbms_output.put_line(p_output); ";
        sqlCode += "end; ";
        
        console.log("Generated SQL for LM_JOB:", sqlCode);
        return sqlCode;
    }
}


function generateAndDisplaySQL() {
    var sqlCode = generateSQL(); 
    console.log(sqlCode); 
    var sqlDisplayDiv = document.getElementById('sql_code_display');
    sqlDisplayDiv.innerText = sqlCode;
    sqlDisplayDiv.style.display = 'block';
}


function generateSQLSP() {
    var selectedType = document.getElementById('storedprocedure_type').value;
    if (selectedType === 'Function_or_Procedure') {
        var selectedSchema = document.getElementById('procedures_schema').value;
        var selectedStoredObjectName = document.getElementById('storedobject_name').value;
        var parameterValues = Array.from(document.getElementById('parameters').getElementsByTagName('input')).map(function(input) {
        return input.value;
        }).join(', ');

        var sqlCode = "BEGIN " + selectedSchema + "." + selectedStoredObjectName + "(" + parameterValues + "); END;";
        
        return sqlCode;

    } else if (selectedType === 'Package') {
        var selectedSchema = document.getElementById('procedures_schema_package').value;
        var selectedPackage = document.getElementById('storedpackage_name').value;
        var selectedStoredObjectName = document.getElementById('storedobject_name_package').value;
        var parameterValues = Array.from(document.getElementById('parameters_package').getElementsByTagName('input')).map(function(input) {
        return input.value;
        }).join(', ');

        var sqlCode = "BEGIN " + selectedSchema + "." + selectedPackage + "." + selectedStoredObjectName + "(" + parameterValues + "); END;";
        
        return sqlCode;
    }
}



function generateAndDisplaySQLSP() {
    var sqlCode = generateSQLSP(); 
    console.log(sqlCode); 
    var sqlDisplayDiv = document.getElementById('sql_code_display');
    sqlDisplayDiv.innerText = sqlCode;
    sqlDisplayDiv.style.display = 'block';
}


function sendSQLToParent() {
    var sqlCode = document.getElementById('sql_code_display').innerText;
    var selectedType = document.getElementById('step_type').value;
    document.getElementById('new_sql_code').value = sqlCode;
    document.getElementById('new_type').value = selectedType;

    document.getElementById("myModal").style.display = "none";
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
    var sqlCode = generateSQL();
    var sqlDisplayDiv = document.getElementById('sql_code_display'); 
    if (sqlDisplayDiv) {
        sqlDisplayDiv.innerText = sqlCode; 
    } else {
        console.error('Error: Unable to find sql_code_display div in modal');
    }
}
