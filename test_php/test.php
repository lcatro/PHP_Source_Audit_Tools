
<?php

    class new_class {
        function try_eval($code) {
            eval($code);
        }
        
        function test($a) {
            phpinfo();
        }

    }

    $a = new new_class();
    $a->try_eval('echo "123";');
    $a->try_eval($_POST['asd']);

    function try_call() {
        $a = $_GET['test'];
        
        include_function($a);
    }

    function try_call2($input) {
        include_function($input);
    }

    function try_include3() {
        $test = $_POST['s'];
        
        try_include8($test);
    }

    include_function('in.php');

?>
