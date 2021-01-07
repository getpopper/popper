import org.junit.Test;
import static org.junit.Assert.*;

public class StringTester {

    @Test
    public void testConcatenate() {
        StringManipulator myUnit = new StringManipulator();

        String result = myUnit.concatenate("one", "two");

        assertEquals("onetwo", result);

    }
}
