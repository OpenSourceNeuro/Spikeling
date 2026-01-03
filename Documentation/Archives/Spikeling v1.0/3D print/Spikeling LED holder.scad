tol = 0.1;
Smoothness = 360;
Wall = 2;

r_LED = 8.9/2;
r_led = 8.0/2;
h_LED = 11.2;
h_LED_base = 2.1;
h_LED_top = 3;

r_photo_base = 6/2;
r_photo = 5/2;
h_photo = 8.9;
h_photo_base = 1;



difference(){
    cylinder (r=r_LED+Wall, h=h_photo, $fn=Smoothness);
    
    #cylinder (r=r_photo_base+tol, h=h_photo_base+tol, $fn=Smoothness);
    translate([0,0,h_photo_base+tol])cylinder(r=r_photo+tol, h=h_photo-h_photo_base+tol, $fn=Smoothness);
}
difference(){
    translate([0,0,h_photo])cylinder(r=r_LED+Wall, h=h_LED, $fn=Smoothness);
    
    translate([0,0,h_photo+h_LED_top])cylinder(r=r_led+tol, h=h_LED-h_LED_top
    , $fn=Smoothness);
    translate([0,0,h_photo+h_LED-h_LED_base])cylinder(r=r_LED+tol, h=h_LED_base, $fn=Smoothness);
    translate([0,0,h_photo+r_led])sphere(r=r_LED+tol, $fn=Smoothness);
    translate([0,0,h_photo])cylinder (r=r_photo+tol, h=h_LED, $fn=Smoothness);
}