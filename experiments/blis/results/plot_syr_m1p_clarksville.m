clear all;

run her_blis
run her_openblas
run her_atlas
%run her_mkl


x_axis( :, 1 ) = data_her_blis( :, 1 );

figure;

flopscol = 3;
msize = 4;
fontsize = 16;
legend_loc = 'NorthEast';
y_begin = 0;
y_end = 10.64;

bli = line( x_axis( :, 1 ), data_her_blis    ( :, flopscol ), ...
                         'Color','k','LineStyle','-' ); % ,'MarkerSize',msize,'Marker','o' );
hold on; ax1 = gca;
obl = line( x_axis( :, 1 ), data_her_openblas( :, flopscol ), ...
            'Parent',ax1,'Color','r','LineStyle','-.','MarkerSize',msize,'Marker','o' );
atl = line( x_axis( :, 1 ), data_her_atlas   ( :, flopscol ), ...
            'Parent',ax1,'Color','m','LineStyle',':','MarkerSize',msize,'Marker','x' );


ylim( ax1, [y_begin y_end] );

leg = legend( ...
[ bli obl atl ], ...
'dsyr\_l (BLIS)', ...
'dsyr\_l (OpenBLAS 0.2.6)', ...
'dsyr\_l (ATLAS 3.10.1)', ...
'Location', legend_loc );

set( leg,'Box','off' );
set( leg,'Color','none' );
set( leg,'FontSize',fontsize );

set( ax1,'FontSize',fontsize );
box on;

titl = title( 'dsyr' );
xlab = xlabel( ax1,'problem size (m = n)' );
ylab = ylabel( ax1,'GFLOPS' );


export_fig( 'fig_syr_m1p_clarksville.pdf', '-grey', '-pdf', '-m2', '-painters', '-transparent' );

hold off;

