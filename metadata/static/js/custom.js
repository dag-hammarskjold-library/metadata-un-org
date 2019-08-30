var springSpace = springSpace || {};
springSpace.la = springSpace.la || {};
springSpace.la.Page = {
    http: 'http:',
    domain: 'ask.un.org',
    iid: 466,
    group_id: 181,
    group_slug: '',
    faq_id: 0,
    qlog_id: 0
};

jQuery(document).ready(function() {

    //event delegation
    jQuery('body').on('click', function(e) {
        var tags = ['A', 'I', 'SPAN', 'B', 'STRONG'];
        var tag = e.target.tagName;
        //links and possible children of links
        if (tags.indexOf(tag) !== -1) {
            var $link = jQuery(e.target).closest('a');
            if ($link.hasClass('imagepreviewlink')) {
                // image previews in FAQs
                e.preventDefault();
                var modal = new springSpace.sui.modal({ url: $link.attr('href'), size: 'large' });
            } else if ($link.hasClass('modallink')) {
                e.preventDefault();
                var modal = new springSpace.sui.modal({ url: $link.attr('href') });
            }
        }
    });

});