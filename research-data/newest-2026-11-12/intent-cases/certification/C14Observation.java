/** NEW 2026-10-26 diagnostic, NOT the original generated test.
 * Repeats the preserved source operation and generated operation on the same
 * fixture, then observes structure. The original generated Java is untouched.
 */
public class C14Observation {
    public static void main(String[] args) {
        org.jsoup.nodes.Document source = org.jsoup.Jsoup.parse("<p>Hello</p>");
        org.jsoup.nodes.Element sourceParagraph = source.selectFirst("p");
        source.text("Replaced");
        source.outputSettings().prettyPrint(false);

        ch.digitalfondue.jfiveparse.Document generated =
            ch.digitalfondue.jfiveparse.JFiveParse.parse("<p>Hello</p>");
        ch.digitalfondue.jfiveparse.Element paragraph =
            (ch.digitalfondue.jfiveparse.Element) generated.getBody().getFirstChild();
        ch.digitalfondue.jfiveparse.Text text =
            (ch.digitalfondue.jfiveparse.Text) paragraph.getFirstChild();
        text.setData("Replaced");

        System.out.println("NEW DIAGNOSTIC, not original generated test");
        System.out.println("fixture=<p>Hello</p>; replacement=Replaced");
        System.out.println("source.documentText=" + source.text());
        System.out.println("generated.documentText=" + generated.getTextContent());
        System.out.println("source.body=" + source.body().outerHtml());
        System.out.println("generated.body=" + ch.digitalfondue.jfiveparse.JFiveParse.serialize(generated.getBody()));
        System.out.println("source.bodyFirstChild=" + source.body().childNode(0).nodeName());
        System.out.println("generated.bodyFirstChild=" + generated.getBody().getFirstChild().getNodeName());
        System.out.println("source.originalParagraphDetached=" + (sourceParagraph.parent() == null));
        System.out.println("generated.originalParagraphStillChild=" + (paragraph.getParentNode() == generated.getBody()));
    }
}
