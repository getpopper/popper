clear all;

run trsm_blis
run trsm_openblas
run trsm_atlas
%run trsm_mkl
%run trsm_blis_nofus_sse_4x4
%run trsm_blis_nofus_fpu_mxn
%run trsm_blis_nofus_sse_mxn
%run trsm_blis_nofus_fpu_4x4

flopscol = 4;
msize = 4;
fontsize = 16;
legend_loc = 'SouthEast';
y_begin = 0;
y_end = 1.2;

baseline                       ( :, 1 ) = data_trsm_blis              ( :, flopscol );
data_trsm_fused_speedup        ( :, 1 ) = data_trsm_blis              ( :, flopscol ) ./ ...
                                          baseline( :, 1 );
data_trsm_nofus_sse_4x4_speedup( :, 1 ) = data_trsm_blis_nofus_sse_4x4( :, flopscol ) ./ ...
                                          baseline( :, 1 );
%data_trsm_nofus_sse_mxn_speedup( :, 1 ) = data_trsm_blis_nofus_sse_mxn( :, flopscol ) ./ ...
%                                          baseline( :, 1 );
%data_trsm_nofus_fpu_4x4_speedup( :, 1 ) = data_trsm_blis_nofus_fpu_4x4( :, flopscol ) ./ ...
%                                          baseline( :, 1 );
data_trsm_nofus_fpu_mxn_speedup( :, 1 ) = data_trsm_blis_nofus_fpu_mxn( :, flopscol ) ./ ...
                                          baseline( :, 1 );

x_axis( :, 1 ) = data_trsm_blis( :, 1 );

figure;


bl3 = line( x_axis( :, 1 ), data_trsm_fused_speedup    ( :, 1 ), ...
                         'Color','k','LineStyle','-' ); % ,'MarkerSize',msize,'Marker','o' );
hold on; ax1 = gca;
bl2 = line( x_axis( :, 1 ), data_trsm_nofus_sse_4x4_speedup( :, 1 ), ...
                         'Color','r','LineStyle','-.','MarkerSize',msize,'Marker','o' );
%bl1 = line( x_axis( :, 1 ), data_trsm_nofus_sse_mxn_speedup( :, 1 ), ...
%                         'Color','r','LineStyle','--','MarkerSize',msize,'Marker','s' );
%bl0 = line( x_axis( :, 1 ), data_trsm_nofus_fpu_4x4_speedup( :, 1 ), ...
%                         'Color','m','LineStyle',':' ); % ,'MarkerSize',msize,'Marker','o' );
blx = line( x_axis( :, 1 ), data_trsm_nofus_fpu_mxn_speedup( :, 1 ), ...
                         'Color','b','LineStyle','--' ); % ,'MarkerSize',msize,'Marker','x' );

ylim( ax1, [y_begin y_end] );

leg = legend( ...
[ bl3 bl2 blx ], ...
'dtrsm\_llnn (fused gemm-trsm)', ...
'dtrsm\_llnn (unfused unrolled trsm, SSE)', ...
'dtrsm\_llnn (unfused generic trsm, FPU)', ...
'Location', legend_loc );

set( leg,'Box','off' );
set( leg,'Color','none' );
set( leg,'FontSize',fontsize );

set( ax1,'FontSize',fontsize );
box on;

titl = title( 'dtrsm' );
xlab = xlabel( ax1,'problem size (m = n)' );
ylab = ylabel( ax1,'Relative performance' );


export_fig( 'fig_trsm_fusing_m1p_n1p_speedup.pdf', '-grey', '-pdf', '-m2', '-painters', '-transparent' );

hold off;

