public class StringApp {
  public static void main(String[] args) {
      StringManipulator strManipulator = new StringManipulator();
      System.out.println("Concatenating strings.");
      System.out.println("\"one\" + \"two\" -> " + strManipulator.concatenate("one","two"));
  }
}
