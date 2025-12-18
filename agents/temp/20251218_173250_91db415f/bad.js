function MyComponent() {
    const [val, setVal] = useState(0); // Missing import useState
    return <div>{val}</div>;
}