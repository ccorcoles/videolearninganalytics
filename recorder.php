<?php 
    if(!$DB = mysql_connect("localhost", "DatabaseName", "P455WORD")) echo "no ha conectado"; 
    mysql_select_db("cimanetvideos", $DB);

    
        $query = sprintf("  INSERT INTO interacciones  
                            SET timestamp_inicial = '%s', random = '%s', video = '%s', timestamp_accion = '%s', accion = '%s', params = '%s'",  
                            $_POST['ti'], $_POST['rnd'], $_POST['vid'], $_POST['ta'], $_POST['acc'], $_POST['prms']);        
        $result = mysql_query($query);
        
   
    mysql_close($DB); 
?>
