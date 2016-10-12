clear all;

run output_trsm_blis
run output_trsm_openblas
run output_trsm_atlas
run output_trsm_mkl


x_axis( :, 1 ) = data_trsm_blis( :, 1 );

figure;

flopscol = 4;
msize = 4;
fontsize = 16;
legend_loc = 'SouthEast';
y_begin = 0;
y_end = 10.64;

bli = line( x_axis( :, 1 ), data_trsm_blis    ( :, flopscol ), ...
                         'Color','k','LineStyle','-' ); % ,'MarkerSize',msize,'Marker','o' );
hold on; ax1 = gca;
obl = line( x_axis( :, 1 ), data_trsm_openblas( :, flopscol ), ...
            'Parent',ax1,'Color','r','LineStyle','-.','MarkerSize',msize,'Marker','o' );
atl = line( x_axis( :, 1 ), data_trsm_atlas   ( :, flopscol ), ...
            'Parent',ax1,'Color','m','LineStyle',':' ,'MarkerSize',msize,'Marker','x' );
mkl = line( x_axis( :, 1 ), data_trsm_mkl     ( :, flopscol ), ...
            'Parent',ax1,'Color','b','LineStyle','--' ); %,'MarkerSize',msize,'Marker','x' );


ylim( ax1, [y_begin y_end] );

leg = legend( ...
[ bli obl atl mkl ], ...
'dtrsm\_llnn (BLIS)', ...
'dtrsm\_llnn (OpenBLAS 0.2.6)', ...
'dtrsm\_llnn (ATLAS 3.10.1)', ...
'dtrsm\_llnn (MKL 11.0 Update 4)', ...
'Location', legend_loc );

set( leg,'Box','off' );
set( leg,'Color','none' );
set( leg,'FontSize',fontsize );

set( ax1,'FontSize',fontsize );
box on;

titl = title( 'dtrsm' );
xlab = xlabel( ax1,'problem size (m = n)' );
ylab = ylabel( ax1,'GFLOPS' );


export_fig( 'fig_trsm_m1p_n1p_clarksville.pdf', '-grey', '-pdf', '-m2', '-painters', '-transparent' );

hold off;

