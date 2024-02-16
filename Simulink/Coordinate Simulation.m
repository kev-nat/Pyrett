n = 15;
pause(5)
for i = 1:n
    clf
    x0 = 0;
    y0 = 0;
    x = out.x;
    y = out.y;
    ny = -y;
    NX = x(i)-cos(atan(y(i)/x(i)));
    NY = y(i)-sin(atan(y(i)/x(i)));
    NY = -NY;
    movementx = [0 NX];
    movementy = [0 NY];
    hold on
    plot(movementx,movementy,'*-')
    
    xlim([0 15])
    ylim([-15 0])
    plot(x(i),ny(i),'.-')
    hold off
    pause(1)
    
end