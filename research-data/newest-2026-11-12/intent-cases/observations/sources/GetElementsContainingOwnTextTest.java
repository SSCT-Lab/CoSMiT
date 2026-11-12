package ch.digitalfondue.jfiveparse;

import java.util.List;

import org.junit.Assert;
import org.junit.Test;

public class GetElementsContainingOwnTextTest {

    @Test
    public void testGetElementsContainingOwnTextId() {
        Document doc = JFiveParse.parse("<div id=1>One</div><div>Two</div>");

        List<Element> elements = doc.getBody().getAllNodesMatching(new NodeMatcher() {
            @Override
            public boolean match(Node node) {
                if (!(node instanceof Element)) {
                    return false;
                }

                for (Node child : node.getChildNodes()) {
                    if (child instanceof Text
                            && "one".equalsIgnoreCase(((Text) child).getData())) {
                        return true;
                    }
                }
                return false;
            }
        });

        Assert.assertEquals(1, elements.size());
        Assert.assertEquals("1", elements.get(0).getId());
    }
}