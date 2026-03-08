import vobject

def txt_to_vcf(numbers,contact_name,vcf_name,per_file,file_count):

    files=[]
    index=0
    counter=1

    for i in range(file_count):

        filename=f"{vcf_name}_{i+1}.vcf"

        f=open(filename,"w")

        for j in range(per_file):

            if index>=len(numbers):
                break

            num=numbers[index]

            f.write(
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"N:{contact_name}{counter}\n"
            f"TEL;TYPE=CELL:{num}\n"
            "END:VCARD\n"
            )

            counter+=1
            index+=1

        f.close()

        files.append(filename)

    return files


def vcf_to_txt(file):

    numbers=[]

    with open(file) as f:

        for vcard in vobject.readComponents(f):

            if hasattr(vcard,"tel"):
                numbers.append(vcard.tel.value)

    out="numbers.txt"

    with open(out,"w") as f:

        for n in numbers:
            f.write(n+"\n")

    return out


def numbers_to_vcf(nums):

    filename="numbers.vcf"

    f=open(filename,"w")

    for i,n in enumerate(nums):

        f.write(
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        f"N:Number{i+1}\n"
        f"TEL;TYPE=CELL:{n}\n"
        "END:VCARD\n"
        )

    f.close()

    return filename