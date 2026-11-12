import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class RandomKeyAssignmentTest {

    @Test
    public void test_random_key_assignment() {
        Map<Double, String> myObj = new HashMap<Double, String>();
        double rand = Math.random();

        myObj.put(rand, "Random Number");

        assertEquals("Random Number", myObj.get(rand));
    }
}