import ch.digitalfondue.jfiveparse.Document;
import ch.digitalfondue.jfiveparse.Element;
import ch.digitalfondue.jfiveparse.JFiveParse;
import ch.digitalfondue.jfiveparse.Text;
import org.junit.Assert;
import org.junit.Test;

public class SetTextPreservesDocumentStructureTest {

    @Test
    public void setTextPreservesDocumentStructure() {
        Document document = JFiveParse.parse("<p>Hello</p>");

        Element paragraph = (Element) document.getBody().getFirstChild();
        Text text = (Text) paragraph.getFirstChild();
        text.setData("Replaced");

        Assert.assertEquals("Replaced", document.getTextContent());
    }
}