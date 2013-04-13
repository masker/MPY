/*-----------------------------------------------------------------------------------

FILE INFORMATION

Description: JavaScript on the "Swatch" WooTheme.
Date Created: 2011-08-24.
Author: Matty.
Since: 1.0.0


TABLE OF CONTENTS

- Featured Slider Setup (SlidesJS)
- Comments Tabber
- Add alt-row styling to tables
- Superfish navigation dropdown

-----------------------------------------------------------------------------------*/

/*-----------------------------------------------------------------------------------*/
/* Featured Slider Setup (SlidesJS) */
/*-----------------------------------------------------------------------------------*/
jQuery( window ).load( function() {

if ( jQuery( '#featured-slider' ).length ) {
	/* Setup dynamic variables. */
	var autoInterval = parseInt( woo_slider_settings.auto ) * 1000;
	var speed = parseInt( woo_slider_settings.speed * 1000 );
	var effect = woo_slider_settings.effect;
	var hoverPause = woo_slider_settings.hoverpause;
	var nextPrev = woo_slider_settings.nextprev;
	var pagination = woo_slider_settings.pagination;
	var autoHeight = woo_slider_settings.autoheight;
	
	if ( hoverPause == 'true' ) { hoverPause = true; } else { hoverPause = false; }
	if ( nextPrev == 'true' ) { nextPrev = true; } else { nextPrev = false; }
	if ( pagination == 'true' ) { pagination = true; } else { pagination = false; }
	if ( autoHeight == 'true' ) { autoHeight = true; } else { autoHeight = false; }
	
	if ( effect != 'slide' && effect != 'fade' ) { effect = 'slide'; } // Sanity check.


	if ( jQuery( '#featured-slider .slide' ).length > 1 ) {

		jQuery( '#featured-slider' ).slides({
			autoHeight: autoHeight,
			effect: effect,		
			hoverPause: hoverPause,
			play: autoInterval,		
			slideSpeed: speed, 
			fadeSpeed: speed, 
			crossfade: false,
			generateNextPrev: nextPrev,
			generatePagination: pagination
		});
	
	} else {
		jQuery( '#featured-slider .slide' ).fadeIn();
	}
}

});

jQuery(document).ready(function(){
/*-----------------------------------------------------------------------------------*/
/* Comments Tabber */
/*-----------------------------------------------------------------------------------*/

if ( jQuery( '#comment-form-tabs' ).length ) {
	jQuery( '#comment-form-tabs' ).tabs();
	
	jQuery( 'a.comment-reply-link' ).click( function () {
		jQuery( '#comment-form-tabs' ).tabs( 'select', '#respond' );
		return false;
	});
}

/*-----------------------------------------------------------------------------------*/
/* Add rel="lightbox" to image links if the lightbox is enabled */
/*-----------------------------------------------------------------------------------*/

if ( jQuery( 'body' ).hasClass( 'has-lightbox' ) && ! jQuery( 'body' ).hasClass( 'portfolio-component' ) ) {
	jQuery( 'a[href$=".jpg"], a[href$=".jpeg"], a[href$=".gif"], a[href$=".png"]' ).each( function () {
		var imageTitle = '';
		if ( jQuery( this ).next().hasClass( 'wp-caption-text' ) ) {
			imageTitle = jQuery( this ).next().text();
		}
		
		jQuery( this ).attr( 'rel', 'lightbox' ).attr( 'title', imageTitle );
	});
	
	jQuery( 'a[rel^="lightbox"]' ).prettyPhoto();
}

/*-----------------------------------------------------------------------------------*/
/* Add alt-row styling to tables */
/*-----------------------------------------------------------------------------------*/

	jQuery( '.entry table tr:odd').addClass( 'alt-table-row' );
	
}); // End jQuery()


/*-----------------------------------------------------------------------------------*/
/* Superfish navigation dropdown */
/*-----------------------------------------------------------------------------------*/
;(function($){$.fn.superfish=function(op){var sf=$.fn.superfish,c=sf.c,$arrow=$(['<span class="',c.arrowClass,'"> &#187;</span>'].join( '')),over=function(){var $$=$(this),menu=getMenu($$);clearTimeout(menu.sfTimer);$$.showSuperfishUl().siblings().hideSuperfishUl()},out=function(){var $$=$(this),menu=getMenu($$),o=sf.op;clearTimeout(menu.sfTimer);menu.sfTimer=setTimeout(function(){o.retainPath=($.inArray($$[0],o.$path)>-1);$$.hideSuperfishUl();if(o.$path.length&&$$.parents(['li.',o.hoverClass].join( '')).length<1){over.call(o.$path)}},o.delay)},getMenu=function($menu){var menu=$menu.parents(['ul.',c.menuClass,':first'].join( ''))[0];sf.op=sf.o[menu.serial];return menu},addArrow=function($a){$a.addClass(c.anchorClass).append($arrow.clone())};return this.each(function(){var s=this.serial=sf.o.length;var o=$.extend({},sf.defaults,op);o.$path=$( 'li.'+o.pathClass,this).slice(0,o.pathLevels).each(function(){$(this).addClass([o.hoverClass,c.bcClass].join( ' ')).filter( 'li:has(ul)').removeClass(o.pathClass)});sf.o[s]=sf.op=o;$( 'li:has(ul)',this)[($.fn.hoverIntent&&!o.disableHI)?'hoverIntent':'hover'](over,out).each(function(){if(o.autoArrows)addArrow($( '>a:first-child',this))}).not( '.'+c.bcClass).hideSuperfishUl();var $a=$( 'a',this);$a.each(function(i){var $li=$a.eq(i).parents( 'li' );$a.eq(i).focus(function(){over.call($li)}).blur(function(){out.call($li)})});o.onInit.call(this)}).each(function(){var menuClasses=[c.menuClass];if(sf.op.dropShadows&&!($.browser.msie&&$.browser.version<7))menuClasses.push(c.shadowClass);$(this).addClass(menuClasses.join( ' '))})};var sf=$.fn.superfish;sf.o=[];sf.op={};sf.IE7fix=function(){var o=sf.op;if($.browser.msie&&$.browser.version>6&&o.dropShadows&&o.animation.opacity!=undefined)this.toggleClass(sf.c.shadowClass+'-off')};sf.c={bcClass:'sf-breadcrumb',menuClass:'sf-js-enabled',anchorClass:'sf-with-ul',arrowClass:'sf-sub-indicator',shadowClass:'sf-shadow'};sf.defaults={hoverClass:'sfHover',pathClass:'overideThisToUse',pathLevels:1,delay:800,animation:{opacity:'show'},speed:'normal',autoArrows:true,dropShadows:true,disableHI:false,onInit:function(){},onBeforeShow:function(){},onShow:function(){},onHide:function(){}};$.fn.extend({hideSuperfishUl:function(){var o=sf.op,not=(o.retainPath===true)?o.$path:'';o.retainPath=false;var $ul=$(['li.',o.hoverClass].join( ''),this).add(this).not(not).removeClass(o.hoverClass).find( '>ul').hide().css( 'visibility','hidden' );o.onHide.call($ul);return this},showSuperfishUl:function(){var o=sf.op,sh=sf.c.shadowClass+'-off',$ul=this.addClass(o.hoverClass).find( '>ul:hidden').css( 'visibility','visible' );sf.IE7fix.call($ul);o.onBeforeShow.call($ul);$ul.animate(o.animation,o.speed,function(){sf.IE7fix.call($ul);o.onShow.call($ul)});return this}})})(jQuery);

if(jQuery().superfish) {
	jQuery(document).ready(function() {
		jQuery( 'ul.nav').superfish({
			delay: 200,
			animation: {opacity:'show', height:'show'},
			speed: 'fast',
			dropShadows: false
		});
	});
}

