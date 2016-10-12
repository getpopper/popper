clear all;

run trmm_blis
run trmm_openblas
run trmm_atlas
%run trmm_mkl


x_axis( :, 1 ) = data_trmm_blis( :, 1 );

figure;

flopscol = 4;
msize = 4;
fontsize = 16;
legend_loc = 'SouthEast';
y_begin = 0;
y_end = 10.64;

bli = line( x_axis( :, 1 ), data_trmm_blis    ( :, flopscol ), ...
                         'Color','k','LineStyle','-' ); % ,'MarkerSize',msize,'Marker','o' );
hold on; ax1 = gca;
obl = line( x_axis( :, 1 ), data_trmm_openblas( :, flopscol ), ...
            'Parent',ax1,'Color','r','LineStyle','-.','MarkerSize',msize,'Marker','o' );
atl = line( x_axis( :, 1 ), data_trmm_atlas   ( :, flopscol ), ...
            'Parent',ax1,'Color','m','LineStyle',':' ,'MarkerSize',msize,'Marker','x' );
mkl = line( x_axis( :, 1 ), data_trmm_mkl     ( :, flopscol ), ...
            'Parent',ax1,'Color','b','LineStyle','--' ); %,'MarkerSize',msize,'Marker','x' );


ylim( ax1, [y_begin y_end] );

leg = legend( ...
[ bli obl atl mkl ], ...
'dtrmm\_llnn (BLIS)', ...
'dtrmm\_llnn (OpenBLAS 0.2.6)', ...
'dtrmm\_llnn (ATLAS 3.10.1)', ...
'dtrmm\_llnn (MKL 11.0 Update 4)', ...
'Location', legend_loc );

set( leg,'Box','off' );
set( leg,'Color','none' );
set( leg,'FontSize',fontsize );

set( ax1,'FontSize',fontsize );
box on;

titl = title( 'dtrmm' );
xlab = xlabel( ax1,'problem size (m = n)' );
ylab = ylabel( ax1,'GFLOPS' );


export_fig( 'fig_trmm_m1p_n1p_clarksville.pdf', '-grey', '-pdf', '-m2', '-painters', '-transparent' );

hold off;

