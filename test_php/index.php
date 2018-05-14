
<html>

    <body>
        
        <?php
        
            function include_function($include_path) {
                $a = $include_path;
                $b = $a;
                
                include $b;
            }
        
            if (isset($_GET['TEST'])) {
                echo 'Take URL parameter test ..';

                exit();
            } else {
                $_GET['TEST'] += 1;
                                  
                echo try_include($_GET['TEST']);
            }
        
            function try_include6() {
                $arg = $_COOKIE['token'];
                
                include_function($arg);
            }
            
            function try_include7($ad) {
                try_call();
            }
        
            function try_include8($ad) {
                try_call2($ad);
            }
        
            include_function($_GET['php']);
            include_function('123.php');
            try_include7($_POST['dddd']);
        
        ?>
        
    </body>

</html>
