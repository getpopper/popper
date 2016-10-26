clear all;

run herk_blis
run herk_openblas
run herk_atlas
%run herk_mkl


x_axis( :, 1 ) = data_herk_blis( :, 1 );

figure;

flopscol = 4;
msize = 4;
fontsize = 16;
legend_loc = 'SouthEast';
y_begin = 0;
y_end = 10.64;

bli = line( x_axis( :, 1 ), data_herk_blis    ( :, flopscol ), ...
                         'Color','k','LineStyle','-' ); % ,'MarkerSize',msize,'Marker','o' );
hold on; ax1 = gca;
obl = line( x_axis( :, 1 ), data_herk_openblas( :, flopscol ), ...
            'Parent',ax1,'Color','r','LineStyle','-.','MarkerSize',msize,'Marker','o' );
atl = line( x_axis( :, 1 ), data_herk_atlas   ( :, flopscol ), ...
            'Parent',ax1,'Color','m','LineStyle',':','MarkerSize',msize,'Marker','x' );


ylim( ax1, [y_begin y_end] );

leg = legend( ...
[ bli obl atl ], ...
'dsyrk\_ln (BLIS)', ...
'dsyrk\_ln (OpenBLAS 0.2.6)', ...
'dsyrk\_ln (ATLAS 3.10.1)', ...
'Location', legend_loc );

set( leg,'Box','off' );
set( leg,'Color','none' );
set( leg,'FontSize',fontsize );

set( ax1,'FontSize',fontsize );
box on;

titl = title( 'dsyrk' );
xlab = xlabel( ax1,'problem size m = k' );
ylab = ylabel( ax1,'GFLOPS' );


hold off;

