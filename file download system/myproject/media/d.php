<?php
// This is a basic PHP script

// Print a message to the screen
echo "Hello, world!";

// Define a variable and assign a value
$name = "Alice";

// Print the value of the variable
echo "My name is " . $name . ".";

// Create a function
function greet($name) {
    echo "Hello, " . $name . "!";
}

// Call the function
greet("Bob");

// Create an array
$fruits = array("apple", "banana", "orange");

// Print the first element of the array
echo $fruits[0];

// Iterate over the elements of the array
foreach ($fruits as $fruit) {
    echo $fruit . "\n";
}
?>