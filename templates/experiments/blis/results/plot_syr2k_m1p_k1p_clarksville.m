clear all;

run her2k_blis
run her2k_openblas
run her2k_atlas
%run her2k_mkl


x_axis( :, 1 ) = data_her2k_blis( :, 1 );

figure;

flopscol = 4;
msize = 4;
fontsize = 16;
legend_loc = 'SouthEast';
y_begin = 0;
y_end = 10.64;

bli = line( x_axis( :, 1 ), data_her2k_blis    ( :, flopscol ), ...
                         'Color','k','LineStyle','-' ); % ,'MarkerSize',msize,'Marker','o' );
hold on; ax1 = gca;
obl = line( x_axis( :, 1 ), data_her2k_openblas( :, flopscol ), ...
            'Parent',ax1,'Color','r','LineStyle','-.','MarkerSize',msize,'Marker','o' );
atl = line( x_axis( :, 1 ), data_her2k_atlas   ( :, flopscol ), ...
            'Parent',ax1,'Color','m','LineStyle',':' ,'MarkerSize',msize,'Marker','x' );


ylim( ax1, [y_begin y_end] );

leg = legend( ...
[ bli obl atl ], ...
'dsyr2k\_ln (BLIS)', ...
'dsyr2k\_ln (OpenBLAS 0.2.6)', ...
'dsyr2k\_ln (ATLAS 3.10.1)', ...
'Location', legend_loc );

set( leg,'Box','off' );
set( leg,'Color','none' );
set( leg,'FontSize',fontsize );

set( ax1,'FontSize',fontsize );
box on;

titl = title( 'dsyr2k' );
xlab = xlabel( ax1,'problem size m = k' );
ylab = ylabel( ax1,'GFLOPS' );


export_fig( 'fig_syr2k_m1p_k1p_clarksville.pdf', '-grey', '-pdf', '-m2', '-painters', '-transparent' );

hold off;

